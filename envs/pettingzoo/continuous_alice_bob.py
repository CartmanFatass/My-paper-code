import gymnasium
import numpy as np
from pettingzoo.utils.env import ParallelEnv
from pettingzoo.utils import wrappers, agent_selector
import pygame

class ContinuousAliceBobEnv(ParallelEnv):
    metadata = {
        "name": "continuous_alice_and_bob_v0",
        "render_modes": ["human"],
        "render_fps": 30,
    }

    def __init__(self, render_mode=None):
        super().__init__()
        self.world_size = 8.0
        self.agent_radius = 0.2
        self.item_radius = 0.3
        self.max_steps = 200

        self.possible_agents = ["alice", "bob"]
        self.agents = self.possible_agents[:]
        self.agent_ids = {name: i for i, name in enumerate(self.possible_agents)}

        self._action_space = {
            agent: gymnasium.spaces.Box(low=-1, high=1, shape=(2,), dtype=np.float32)
            for agent in self.possible_agents
        }
        self._observation_space = {
            agent: gymnasium.spaces.Box(low=-np.inf, high=np.inf, shape=(12,), dtype=np.float32)
            for agent in self.possible_agents
        }

        self.render_mode = render_mode
        if self.render_mode == "human":
            self.screen = None
            self.clock = None

    def get_state_dim(self):
        # state: agent_pos (4) + button_pos (4) + diamond_pos (4) + button_pressed (2) + diamond_collected (2)
        return 16

    def get_obs_dim(self):
        return self._observation_space["alice"].shape[0]

    def action_space(self, agent):
        return self._action_space[agent]

    def observation_space(self, agent):
        return self._observation_space[agent]

    def _get_state(self):
        # A reasonable global state would be the concatenation of all unique info
        return np.concatenate([
            self.agent_pos.flatten(),
            self.button_pos.flatten(),
            self.diamond_pos.flatten(),
            self.button_pressed.astype(np.float32),
            self.diamond_collected.astype(np.float32)
        ]).astype(np.float32)

    def reset(self, seed=None, options=None):
        self.agents = self.possible_agents[:]
        self.steps = 0

        # Item positions
        self.button_pos = np.array([[2, 6], [6, 6]], dtype=np.float32)
        self.diamond_pos = np.array([[2, 2], [6, 2]], dtype=np.float32)

        # Agent positions
        self.agent_pos = np.array([[2, 1], [6, 1]], dtype=np.float32)

        # State
        self.button_pressed = np.array([False, False])
        self.diamond_collected = np.array([False, False])

        observations = self._get_obs()
        infos = self._get_infos()
        return observations, infos

    def _get_obs(self):
        obs = {}
        for agent_name in self.agents:
            agent_idx = self.agent_ids[agent_name]
            other_agent_idx = 1 - agent_idx
            
            # obs: my_pos, other_pos, button0_pos, button1_pos, diamond0_pos, diamond1_pos
            # Simplified to global state for all agents
            # obs: my_pos, other_pos, button0_pos, button1_pos, diamond0_pos, diamond1_pos
            # Total 6 * 2 = 12 dimensions
            obs_vec = np.concatenate([
                self.agent_pos[agent_idx],
                self.agent_pos[other_agent_idx],
                self.button_pos[0],
                self.button_pos[1],
                self.diamond_pos[0],
                self.diamond_pos[1],
            ])
            obs[agent_name] = obs_vec.astype(np.float32)
        return obs

    def _get_infos(self):
        return {agent: {} for agent in self.agents}

    def step(self, actions):
        # Move agents
        for agent_name, action in actions.items():
            agent_idx = self.agent_ids[agent_name]
            self.agent_pos[agent_idx] += action
            self.agent_pos[agent_idx] = np.clip(self.agent_pos[agent_idx], 0, self.world_size)

        # Check for button presses
        self.button_pressed.fill(False)
        for i in range(2): # For each button
            for j in range(2): # For each agent
                if np.linalg.norm(self.agent_pos[j] - self.button_pos[i]) < self.item_radius:
                    self.button_pressed[i] = True

        # Check for diamond collections
        reward = 0.0
        previously_collected = self.diamond_collected.copy()
        for i in range(2): # For each diamond
            if not self.diamond_collected[i] and self.button_pressed[i]:
                for j in range(2): # For each agent
                    if np.linalg.norm(self.agent_pos[j] - self.diamond_pos[i]) < self.item_radius:
                        self.diamond_collected[i] = True
        
        # Sparse reward logic
        if np.all(self.diamond_collected) and not np.all(previously_collected):
             reward = 1.0

        self.steps += 1
        terminations = {agent: self.steps >= self.max_steps for agent in self.agents}
        truncations = {agent: False for agent in self.agents}
        rewards = {agent: reward for agent in self.agents}

        observations = self._get_obs()
        infos = self._get_infos()

        if self.render_mode == "human":
            self.render()

        return observations, rewards, terminations, truncations, infos

    def render(self):
        if self.render_mode != "human":
            return

        if self.screen is None:
            pygame.init()
            self.screen = pygame.display.set_mode((600, 600))
            pygame.display.set_caption("Continuous Alice and Bob")
            self.clock = pygame.time.Clock()

        self.screen.fill((255, 255, 255))
        scale = 600 / self.world_size

        # Draw buttons
        for i, pos in enumerate(self.button_pos):
            color = (0, 255, 0) if self.button_pressed[i] else (100, 100, 100)
            pygame.draw.circle(self.screen, color, (pos * scale).astype(int), int(self.item_radius * scale))

        # Draw diamonds
        for i, pos in enumerate(self.diamond_pos):
            if not self.diamond_collected[i]:
                color = (0, 0, 255)
                pygame.draw.rect(self.screen, color, (pos[0]*scale - 10, pos[1]*scale - 10, 20, 20))

        # Draw agents
        colors = [(255, 0, 0), (255, 165, 0)] # Red for Alice, Orange for Bob
        for i, pos in enumerate(self.agent_pos):
            pygame.draw.circle(self.screen, colors[i], (pos * scale).astype(int), int(self.agent_radius * scale))

        pygame.display.flip()
        self.clock.tick(self.metadata["render_fps"])

    def close(self):
        if self.screen:
            pygame.quit()
            self.screen = None
