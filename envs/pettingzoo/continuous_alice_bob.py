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

    def __init__(self, render_mode=None, vision_range=3.0):
        super().__init__()
        self.world_size = 8.0
        self.agent_radius = 0.5  # 1x1 collision volume (diameter = 1.0)
        self.item_radius = 0.5   # 1x1 collision volume (diameter = 1.0)
        self.max_steps = 200
        self.vision_range = vision_range  # 智能体的视野范围

        self.possible_agents = ["alice", "bob"]
        self.agents = self.possible_agents[:]
        self.agent_ids = {name: i for i, name in enumerate(self.possible_agents)}
        self.np_random = np.random.RandomState()

        self._action_space = {
            agent: gymnasium.spaces.Box(low=-1, high=1, shape=(2,), dtype=np.float32)
            for agent in self.possible_agents
        }
        # 修改观测空间维度：局部观测维度更小
        # 新的局部观测：my_pos(2) + visible_items(最多6个物体*3维=18) = 20维
        self._observation_space = {
            agent: gymnasium.spaces.Box(low=-np.inf, high=np.inf, shape=(20,), dtype=np.float32)
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
        if seed is not None:
            self.np_random = np.random.RandomState(seed)
            
        self.agents = self.possible_agents[:]
        self.steps = 0

        # Fixed item positions according to paper requirements
        # Left-top: blue button, Right-top: red button
        # Left-bottom: red diamond, Right-bottom: blue diamond
        self.button_pos = np.array([[1.0, 7.0], [7.0, 7.0]], dtype=np.float32)  # [blue, red]
        self.diamond_pos = np.array([[1.0, 1.0], [7.0, 1.0]], dtype=np.float32)  # [red, blue]
        
        # Color mapping: 0=blue, 1=red
        self.button_colors = np.array([0, 1])  # [blue, red]
        self.diamond_colors = np.array([1, 0])  # [red, blue]

        # Random agent positions (avoiding overlap with items and each other)
        self.agent_pos = self._generate_random_agent_positions()

        # State
        self.button_pressed = np.array([False, False])
        self.diamond_collected = np.array([False, False])

        observations = self._get_obs()
        infos = self._get_infos()
        return observations, infos

    def _generate_random_agent_positions(self):
        """Generate random positions for agents, avoiding overlap with items and each other"""
        positions = []
        max_attempts = 100
        
        # All item positions to avoid
        avoid_positions = np.concatenate([self.button_pos, self.diamond_pos])
        
        for agent_idx in range(2):
            for attempt in range(max_attempts):
                # Generate random position within world bounds, considering agent radius
                pos = self.np_random.uniform(
                    low=self.agent_radius, 
                    high=self.world_size - self.agent_radius, 
                    size=2
                ).astype(np.float32)
                
                # Check if position is too close to items
                too_close_to_items = False
                for item_pos in avoid_positions:
                    if np.linalg.norm(pos - item_pos) < (self.agent_radius + self.item_radius):
                        too_close_to_items = True
                        break
                
                # Check if position is too close to other agents
                too_close_to_agents = False
                for other_pos in positions:
                    if np.linalg.norm(pos - other_pos) < (2 * self.agent_radius):
                        too_close_to_agents = True
                        break
                
                if not too_close_to_items and not too_close_to_agents:
                    positions.append(pos)
                    break
            else:
                # If we couldn't find a good position, use a fallback
                fallback_positions = [
                    np.array([4.0, 4.0], dtype=np.float32),
                    np.array([4.0, 5.0], dtype=np.float32)
                ]
                positions.append(fallback_positions[agent_idx])
        
        return np.array(positions)

    def _get_obs(self):
        obs = {}
        for agent_name in self.agents:
            agent_idx = self.agent_ids[agent_name]
            my_pos = self.agent_pos[agent_idx]
            
            # 局部观测：只包含智能体自身位置和视野范围内的物体
            obs_components = [my_pos]  # 自己的位置 (2维)
            
            # 检查视野范围内的所有物体
            # 每个物体用3维表示：[相对x, 相对y, 物体类型]
            # 物体类型：0=其他智能体, 1=按钮, 2=钻石
            visible_items = []
            
            # 检查其他智能体
            for other_idx in range(len(self.agent_pos)):
                if other_idx != agent_idx:
                    other_pos = self.agent_pos[other_idx]
                    distance = np.linalg.norm(other_pos - my_pos)
                    if distance <= self.vision_range:
                        relative_pos = other_pos - my_pos
                        visible_items.append([relative_pos[0], relative_pos[1], 0.0])  # 类型0=其他智能体
            
            # 检查按钮
            for button_idx, button_pos in enumerate(self.button_pos):
                distance = np.linalg.norm(button_pos - my_pos)
                if distance <= self.vision_range:
                    relative_pos = button_pos - my_pos
                    # 按钮状态编码：1.0=未按下, 2.0=已按下
                    button_state = 2.0 if self.button_pressed[button_idx] else 1.0
                    visible_items.append([relative_pos[0], relative_pos[1], button_state])
            
            # 检查钻石
            for diamond_idx, diamond_pos in enumerate(self.diamond_pos):
                if not self.diamond_collected[diamond_idx]:  # 只有未收集的钻石才可见
                    distance = np.linalg.norm(diamond_pos - my_pos)
                    if distance <= self.vision_range:
                        relative_pos = diamond_pos - my_pos
                        visible_items.append([relative_pos[0], relative_pos[1], 3.0])  # 类型3=钻石
            
            # 填充到固定长度（最多6个物体）
            max_visible_items = 6
            while len(visible_items) < max_visible_items:
                visible_items.append([0.0, 0.0, -1.0])  # 用-1表示空槽位
            
            # 如果超过最大数量，只保留最近的物体
            if len(visible_items) > max_visible_items:
                # 按距离排序，保留最近的
                distances = [np.linalg.norm([item[0], item[1]]) for item in visible_items]
                sorted_indices = np.argsort(distances)
                visible_items = [visible_items[i] for i in sorted_indices[:max_visible_items]]
            
            # 展平可见物体列表
            visible_items_flat = np.array(visible_items).flatten()  # 6*3=18维
            
            # 组合最终观测：my_pos(2) + visible_items(18) = 20维
            obs_vec = np.concatenate([my_pos, visible_items_flat])
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

        # Check for diamond collections with color matching
        reward = 0.0
        previously_collected = self.diamond_collected.copy()
        
        # Check each diamond for collection
        for diamond_idx in range(2):
            if not self.diamond_collected[diamond_idx]:
                diamond_color = self.diamond_colors[diamond_idx]
                
                # Check if any button of the same color is pressed
                same_color_button_pressed = False
                for button_idx in range(2):
                    if (self.button_colors[button_idx] == diamond_color and 
                        self.button_pressed[button_idx]):
                        same_color_button_pressed = True
                        break
                
                # If same color button is pressed, check if any agent touches this diamond
                if same_color_button_pressed:
                    for agent_idx in range(2):
                        if np.linalg.norm(self.agent_pos[agent_idx] - self.diamond_pos[diamond_idx]) < self.item_radius:
                            self.diamond_collected[diamond_idx] = True
                            break
        
        # Sparse reward logic - give reward when all diamonds are collected
        if np.all(self.diamond_collected) and not np.all(previously_collected):
             reward = 1.0

        self.steps += 1

        # Task is done if all diamonds are collected
        task_completed = np.all(self.diamond_collected)
        
        # Episode is truncated if max steps are reached without task completion
        time_limit_reached = self.steps >= self.max_steps and not task_completed

        terminations = {agent: task_completed for agent in self.agents}
        truncations = {agent: time_limit_reached for agent in self.agents}
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

        # Color definitions: 0=blue, 1=red
        color_map = {0: (0, 0, 255), 1: (255, 0, 0)}  # blue, red
        pressed_color_map = {0: (0, 150, 255), 1: (255, 150, 150)}  # lighter versions when pressed

        # Draw buttons with proper colors
        for i, pos in enumerate(self.button_pos):
            button_color = self.button_colors[i]
            if self.button_pressed[i]:
                color = pressed_color_map[button_color]
            else:
                color = color_map[button_color]
            pygame.draw.circle(self.screen, color, (pos * scale).astype(int), int(self.item_radius * scale))

        # Draw diamonds with proper colors
        for i, pos in enumerate(self.diamond_pos):
            if not self.diamond_collected[i]:
                diamond_color = self.diamond_colors[i]
                color = color_map[diamond_color]
                # Draw diamond as a rotated square
                diamond_size = int(self.item_radius * scale)
                center = (pos * scale).astype(int)
                # Create diamond shape points
                points = [
                    (center[0], center[1] - diamond_size),  # top
                    (center[0] + diamond_size, center[1]),  # right
                    (center[0], center[1] + diamond_size),  # bottom
                    (center[0] - diamond_size, center[1])   # left
                ]
                pygame.draw.polygon(self.screen, color, points)

        # Draw agents
        colors = [(255, 0, 0), (255, 165, 0)] # Red for Alice, Orange for Bob
        for i, pos in enumerate(self.agent_pos):
            pygame.draw.circle(self.screen, colors[i], (pos * scale).astype(int), int(self.agent_radius * scale))

        pygame.display.flip()
        self.clock.tick(self.metadata["render_fps"])

    def close(self):
        if hasattr(self, 'screen') and self.screen:
            pygame.quit()
            self.screen = None
