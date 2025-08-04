"""
Critical Fix for HMASD Intrinsic Reward Computation

This script identifies and fixes the fundamental issue preventing HMASD from learning:
the intrinsic reward computation is using raw discriminator log probabilities instead 
of proper mutual information estimation as described in the paper.
"""

import torch
import torch.nn.functional as F
import numpy as np
from config_continuous_alice_bob import Config
from hmasd.agent import HMASDAgent
from envs.pettingzoo.continuous_alice_bob import ContinuousAliceBobEnv

def analyze_current_intrinsic_rewards():
    """Analyze the current intrinsic reward computation issues"""
    print("=== HMASD Intrinsic Reward Analysis ===\n")
    
    # Initialize
    config = Config()
    env = ContinuousAliceBobEnv()
    config.state_dim = env.get_state_dim()
    config.obs_dim = env.get_obs_dim()
    config.action_dim = env.action_space('alice').shape[0]
    
    agent = HMASDAgent(config, debug=False)
    
    # Test current implementation
    observations, _ = env.reset()
    state = env._get_state()
    
    print("1. Current Implementation Issues:")
    print("   - All intrinsic rewards are negative")
    print("   - Uses raw log probabilities: log q_D(Z|s) and log q_d(z|o,Z)")
    print("   - Should use mutual information: log q_D(Z|s) - log p(Z)")
    print("   - No baseline subtraction for variance reduction")
    print("   - No reward normalization or clipping")
    
    # Demonstrate the issue
    actions = {
        'alice': env.action_space('alice').sample(),
        'bob': env.action_space('bob').sample()
    }
    next_observations, rewards, terminations, truncations, infos = env.step(actions)
    next_state = env._get_state()
    
    print("\n2. Current Reward Components:")
    for team_skill in range(config.n_Z):
        for agent_skill in range(config.n_z):
            intrinsic_reward, env_comp, team_disc_comp, ind_disc_comp = agent._compute_intrinsic_reward(
                next_state, rewards['alice'], next_observations['alice'], team_skill, agent_skill
            )
            print(f"   Team={team_skill}, Agent={agent_skill}: Total={intrinsic_reward:.4f} "
                  f"(env={env_comp:.4f}, team_disc={team_disc_comp:.4f}, ind_disc={ind_disc_comp:.4f})")
    
    return agent, env, config

def create_fixed_intrinsic_reward_method():
    """Create the corrected intrinsic reward computation method"""
    
    def _compute_intrinsic_reward_fixed(self, next_state, reward, next_obs, team_skill, agent_skill):
        """
        Fixed intrinsic reward computation using proper mutual information estimation
        
        Key fixes:
        1. Use mutual information: I(s;z) = log q(z|s) - log p(z) instead of raw log q(z|s)
        2. Add baseline subtraction for variance reduction
        3. Add reward normalization and clipping
        4. Use running averages for stable baselines
        """
        with torch.no_grad():
            try:
                # === Team Discriminator Reward (Fixed) ===
                next_state_tensor = torch.FloatTensor(next_state).unsqueeze(0).to(self.device)
                team_disc_logits = self.team_discriminator(next_state_tensor)
                
                # Use log_softmax for numerical stability
                team_disc_log_probs = F.log_softmax(team_disc_logits, dim=-1)
                team_skill_log_prob = team_disc_log_probs[0, team_skill]
                
                # CRITICAL FIX: Use mutual information instead of raw log probability
                # I(s;Z) = log q_D(Z|s) - log p(Z)
                # Assume uniform prior: log p(Z) = -log(n_Z)
                team_skill_prior_log_prob = -np.log(self.config.n_Z)
                team_mutual_info = team_skill_log_prob.item() - team_skill_prior_log_prob
                
                # === Individual Discriminator Reward (Fixed) ===
                agent_obs_tensor = torch.FloatTensor(next_obs).unsqueeze(0).to(self.device)
                team_skill_tensor = torch.tensor(team_skill, device=self.device)
                agent_disc_logits = self.individual_discriminator(agent_obs_tensor, team_skill_tensor)
                
                agent_disc_log_probs = F.log_softmax(agent_disc_logits, dim=-1)
                agent_skill_log_prob = agent_disc_log_probs[0, agent_skill]
                
                # CRITICAL FIX: Use mutual information for individual skills too
                # I(o;z|Z) = log q_d(z|o,Z) - log p(z|Z)
                # Assume uniform conditional prior: log p(z|Z) = -log(n_z)
                agent_skill_prior_log_prob = -np.log(self.config.n_z)
                agent_mutual_info = agent_skill_log_prob.item() - agent_skill_prior_log_prob
                
                # === Baseline Subtraction for Variance Reduction ===
                # Initialize running baselines if not exists
                if not hasattr(self, 'team_disc_baseline'):
                    self.team_disc_baseline = 0.0
                    self.ind_disc_baseline = 0.0
                    self.baseline_update_rate = 0.01
                
                # Update baselines with exponential moving average
                self.team_disc_baseline = (1 - self.baseline_update_rate) * self.team_disc_baseline + \
                                        self.baseline_update_rate * team_mutual_info
                self.ind_disc_baseline = (1 - self.baseline_update_rate) * self.ind_disc_baseline + \
                                       self.baseline_update_rate * agent_mutual_info
                
                # Subtract baselines
                team_disc_reward = team_mutual_info - self.team_disc_baseline
                ind_disc_reward = agent_mutual_info - self.ind_disc_baseline
                
                # === Reward Normalization and Clipping ===
                # Initialize running statistics if not exists
                if not hasattr(self, 'team_disc_reward_std'):
                    self.team_disc_reward_std = 1.0
                    self.ind_disc_reward_std = 1.0
                    self.reward_std_update_rate = 0.01
                
                # Update reward standard deviations
                self.team_disc_reward_std = (1 - self.reward_std_update_rate) * self.team_disc_reward_std + \
                                          self.reward_std_update_rate * abs(team_disc_reward)
                self.ind_disc_reward_std = (1 - self.reward_std_update_rate) * self.ind_disc_reward_std + \
                                         self.reward_std_update_rate * abs(ind_disc_reward)
                
                # Normalize rewards
                team_disc_reward_normalized = team_disc_reward / (self.team_disc_reward_std + 1e-8)
                ind_disc_reward_normalized = ind_disc_reward / (self.ind_disc_reward_std + 1e-8)
                
                # Clip rewards to prevent extreme values
                team_disc_reward_clipped = np.clip(team_disc_reward_normalized, -5.0, 5.0)
                ind_disc_reward_clipped = np.clip(ind_disc_reward_normalized, -5.0, 5.0)
                
                # === Final Reward Computation ===
                env_component = self.config.lambda_e * reward
                team_disc_component = self.config.lambda_D * team_disc_reward_clipped
                ind_disc_component = self.config.lambda_d * ind_disc_reward_clipped
                
                intrinsic_reward = env_component + team_disc_component + ind_disc_component
                
                # Ensure finite values
                if not np.isfinite(intrinsic_reward):
                    intrinsic_reward = env_component
                    team_disc_component = 0.0
                    ind_disc_component = 0.0
                
                return intrinsic_reward, env_component, team_disc_component, ind_disc_component
                
            except Exception as e:
                print(f"Error in fixed intrinsic reward computation: {e}")
                env_component = self.config.lambda_e * reward
                return env_component, env_component, 0.0, 0.0
    
    return _compute_intrinsic_reward_fixed

def test_fixed_implementation():
    """Test the fixed intrinsic reward implementation"""
    print("\n=== Testing Fixed Implementation ===\n")
    
    agent, env, config = analyze_current_intrinsic_rewards()
    
    # Apply the fix
    fixed_method = create_fixed_intrinsic_reward_method()
    agent._compute_intrinsic_reward = fixed_method.__get__(agent, HMASDAgent)
    
    # Test the fixed implementation
    observations, _ = env.reset()
    state = env._get_state()
    
    actions = {
        'alice': env.action_space('alice').sample(),
        'bob': env.action_space('bob').sample()
    }
    next_observations, rewards, terminations, truncations, infos = env.step(actions)
    next_state = env._get_state()
    
    print("3. Fixed Reward Components (after applying mutual information fix):")
    for team_skill in range(config.n_Z):
        for agent_skill in range(config.n_z):
            intrinsic_reward, env_comp, team_disc_comp, ind_disc_comp = agent._compute_intrinsic_reward(
                next_state, rewards['alice'], next_observations['alice'], team_skill, agent_skill
            )
            print(f"   Team={team_skill}, Agent={agent_skill}: Total={intrinsic_reward:.4f} "
                  f"(env={env_comp:.4f}, team_disc={team_disc_comp:.4f}, ind_disc={ind_disc_comp:.4f})")
    
    print("\n4. Key Improvements:")
    print("   ✓ Uses proper mutual information: I(s;z) = log q(z|s) - log p(z)")
    print("   ✓ Adds baseline subtraction for variance reduction")
    print("   ✓ Implements reward normalization and clipping")
    print("   ✓ Prevents extreme reward values")
    print("   ✓ Should enable positive learning signals")

def generate_patch_code():
    """Generate the actual code patch to apply to agent.py"""
    print("\n=== Code Patch for agent.py ===\n")
    
    patch_code = '''
def _compute_intrinsic_reward(self, next_state, reward, next_obs, team_skill, agent_skill):
    """
    【CRITICAL FIX】Fixed intrinsic reward computation using proper mutual information estimation
    
    Key fixes:
    1. Use mutual information: I(s;z) = log q(z|s) - log p(z) instead of raw log q(z|s)
    2. Add baseline subtraction for variance reduction
    3. Add reward normalization and clipping
    4. Use running averages for stable baselines
    """
    with torch.no_grad():
        try:
            # === Team Discriminator Reward (Fixed) ===
            next_state_tensor = torch.FloatTensor(next_state).unsqueeze(0).to(self.device)
            team_disc_logits = self.team_discriminator(next_state_tensor)
            
            # Use log_softmax for numerical stability
            team_disc_log_probs = F.log_softmax(team_disc_logits, dim=-1)
            team_skill_log_prob = team_disc_log_probs[0, team_skill]
            
            # CRITICAL FIX: Use mutual information instead of raw log probability
            # I(s;Z) = log q_D(Z|s) - log p(Z)
            # Assume uniform prior: log p(Z) = -log(n_Z)
            team_skill_prior_log_prob = -np.log(self.config.n_Z)
            team_mutual_info = team_skill_log_prob.item() - team_skill_prior_log_prob
            
            # === Individual Discriminator Reward (Fixed) ===
            agent_obs_tensor = torch.FloatTensor(next_obs).unsqueeze(0).to(self.device)
            team_skill_tensor = torch.tensor(team_skill, device=self.device)
            agent_disc_logits = self.individual_discriminator(agent_obs_tensor, team_skill_tensor)
            
            agent_disc_log_probs = F.log_softmax(agent_disc_logits, dim=-1)
            agent_skill_log_prob = agent_disc_log_probs[0, agent_skill]
            
            # CRITICAL FIX: Use mutual information for individual skills too
            # I(o;z|Z) = log q_d(z|o,Z) - log p(z|Z)
            # Assume uniform conditional prior: log p(z|Z) = -log(n_z)
            agent_skill_prior_log_prob = -np.log(self.config.n_z)
            agent_mutual_info = agent_skill_log_prob.item() - agent_skill_prior_log_prob
            
            # === Baseline Subtraction for Variance Reduction ===
            # Initialize running baselines if not exists
            if not hasattr(self, 'team_disc_baseline'):
                self.team_disc_baseline = 0.0
                self.ind_disc_baseline = 0.0
                self.baseline_update_rate = 0.01
            
            # Update baselines with exponential moving average
            self.team_disc_baseline = (1 - self.baseline_update_rate) * self.team_disc_baseline + \\
                                    self.baseline_update_rate * team_mutual_info
            self.ind_disc_baseline = (1 - self.baseline_update_rate) * self.ind_disc_baseline + \\
                                   self.baseline_update_rate * agent_mutual_info
            
            # Subtract baselines
            team_disc_reward = team_mutual_info - self.team_disc_baseline
            ind_disc_reward = agent_mutual_info - self.ind_disc_baseline
            
            # === Reward Normalization and Clipping ===
            # Initialize running statistics if not exists
            if not hasattr(self, 'team_disc_reward_std'):
                self.team_disc_reward_std = 1.0
                self.ind_disc_reward_std = 1.0
                self.reward_std_update_rate = 0.01
            
            # Update reward standard deviations
            self.team_disc_reward_std = (1 - self.reward_std_update_rate) * self.team_disc_reward_std + \\
                                      self.reward_std_update_rate * abs(team_disc_reward)
            self.ind_disc_reward_std = (1 - self.reward_std_update_rate) * self.ind_disc_reward_std + \\
                                     self.reward_std_update_rate * abs(ind_disc_reward)
            
            # Normalize rewards
            team_disc_reward_normalized = team_disc_reward / (self.team_disc_reward_std + 1e-8)
            ind_disc_reward_normalized = ind_disc_reward / (self.ind_disc_reward_std + 1e-8)
            
            # Clip rewards to prevent extreme values
            team_disc_reward_clipped = np.clip(team_disc_reward_normalized, -5.0, 5.0)
            ind_disc_reward_clipped = np.clip(ind_disc_reward_normalized, -5.0, 5.0)
            
            # === Final Reward Computation ===
            env_component = self.config.lambda_e * reward
            team_disc_component = self.config.lambda_D * team_disc_reward_clipped
            ind_disc_component = self.config.lambda_d * ind_disc_reward_clipped
            
            intrinsic_reward = env_component + team_disc_component + ind_disc_component
            
            # Ensure finite values
            if not np.isfinite(intrinsic_reward):
                intrinsic_reward = env_component
                team_disc_component = 0.0
                ind_disc_component = 0.0
            
            return intrinsic_reward, env_component, team_disc_component, ind_disc_component
            
        except Exception as e:
            print(f"Error in fixed intrinsic reward computation: {e}")
            env_component = self.config.lambda_e * reward
            return env_component, env_component, 0.0, 0.0
'''
    
    print("Replace the existing _compute_intrinsic_reward method in hmasd/agent.py with:")
    print(patch_code)

if __name__ == "__main__":
    analyze_current_intrinsic_rewards()
    test_fixed_implementation()
    generate_patch_code()
