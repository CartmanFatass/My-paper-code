"""
基于流形的目标导向HMASD代理
将原有的技能发现机制重构为目标导向的强化学习框架
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from torch.optim import Adam
from torch.distributions import Normal
import os
import random
from collections import deque
from torch.utils.tensorboard import SummaryWriter

# 确保在多进程环境中使用安全的matplotlib后端
import matplotlib
if matplotlib.get_backend() != 'Agg':
    matplotlib.use('Agg')

from hmasd.logging import main_logger
from manifold_hmasd.vae import StateManifoldVAE
from manifold_hmasd.her_replay_buffer import HERReplayBuffer, create_manifold_her_buffer
from hmasd.utils import clone_replay_data

STRICT_CHECKPOINT_VERSION = 4
MANIFOLD_LEGACY_WARM_START_KEYS = frozenset({
    'policy_state_dict', 'optimizer_state_dict', 'config', 'global_step', 'training_info'
})


def _capture_torch_sampling_rng_state():
    cuda_initialized = bool(torch.cuda.is_initialized())
    cuda_states = torch.cuda.get_rng_state_all() if cuda_initialized else []
    return {
        'cpu': torch.get_rng_state().clone(),
        'cuda_initialized': cuda_initialized,
        'cuda_device_count': len(cuda_states),
        'cuda': [state.clone() for state in cuda_states],
    }


def _validate_torch_sampling_rng_state(state):
    required = {'cpu', 'cuda_initialized', 'cuda_device_count', 'cuda'}
    if not isinstance(state, dict) or set(state) != required:
        raise ValueError("invalid Torch policy-sampling RNG checkpoint schema")
    cpu = state['cpu']
    if not torch.is_tensor(cpu) or cpu.dtype != torch.uint8 or cpu.ndim != 1 or not cpu.numel():
        raise ValueError("invalid Torch CPU policy-sampling RNG state")
    if not isinstance(state['cuda_initialized'], bool):
        raise ValueError("invalid Torch CUDA RNG initialization marker")
    if not isinstance(state['cuda_device_count'], int) or state['cuda_device_count'] < 0:
        raise ValueError("invalid Torch CUDA RNG device count")
    cuda_states = state['cuda']
    if not isinstance(cuda_states, list):
        raise ValueError("invalid Torch CUDA policy-sampling RNG state list")
    if not state['cuda_initialized']:
        if state['cuda_device_count'] != 0 or cuda_states:
            raise ValueError("Torch checkpoint has CUDA RNG states without initialization")
        return
    if not torch.cuda.is_available():
        raise ValueError("Torch checkpoint requires CUDA RNG state but CUDA is unavailable")
    runtime_count = torch.cuda.device_count()
    if runtime_count != state['cuda_device_count'] or len(cuda_states) != runtime_count:
        raise ValueError("Torch CUDA RNG device-count/state mismatch")
    for cuda_state in cuda_states:
        if (
            not torch.is_tensor(cuda_state) or cuda_state.dtype != torch.uint8
            or cuda_state.ndim != 1 or not cuda_state.numel()
        ):
            raise ValueError("invalid Torch CUDA policy-sampling RNG state")


def _restore_torch_sampling_rng_state(state):
    torch.set_rng_state(state['cpu'].cpu())
    if state['cuda_initialized']:
        torch.cuda.set_rng_state_all([item.cpu() for item in state['cuda']])


def _canonical_device_identity(device):
    device = torch.device(device)
    index = device.index
    if device.type == 'cuda' and index is None:
        index = torch.cuda.current_device()
    return {'type': device.type, 'index': index}


def _canonical_module_device(module, label):
    devices = {parameter.device for parameter in module.parameters()}
    devices.update(buffer.device for buffer in module.buffers())
    if len(devices) != 1:
        raise ValueError(f"{label} must have exactly one policy parameter device")
    return _canonical_device_identity(next(iter(devices)))

class GoalConditionedPolicy(nn.Module):
    """
    目标导向策略网络
    输入：观测 + 目标状态
    输出：动作分布
    """
    def __init__(self, obs_dim, goal_dim, action_dim, hidden_dim=128, use_goal_conditioning=True):
        super(GoalConditionedPolicy, self).__init__()
        
        self.obs_dim = obs_dim
        self.goal_dim = goal_dim
        self.action_dim = action_dim
        self.use_goal_conditioning = use_goal_conditioning
        
        # 输入维度：观测 + 目标状态（如果启用目标导向）
        input_dim = obs_dim + (goal_dim if use_goal_conditioning else 0)
        
        # 特征提取网络
        self.feature_net = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU()
        )
        
        # 动作均值和标准差
        self.action_mean = nn.Linear(hidden_dim, action_dim)
        self.action_log_std = nn.Linear(hidden_dim, action_dim)
        
        # 价值函数（状态-动作价值）
        self.value_head = nn.Linear(hidden_dim, 1)
        
        # 权重初始化
        self._init_weights()
    
    def _init_weights(self):
        """初始化网络权重"""
        for m in self.modules():
            if isinstance(m, nn.Linear):
                nn.init.orthogonal_(m.weight, gain=1.0)
                if m.bias is not None:
                    nn.init.zeros_(m.bias)
        
        # 动作标准差初始化为较小值
        nn.init.constant_(self.action_log_std.bias, -1.0)
    
    def _distribution_value(self, obs, goal=None):
        obs = obs.float()
        if self.use_goal_conditioning and goal is not None:
            goal = goal.float()
            policy_input = torch.cat([obs, goal], dim=-1)
        else:
            policy_input = obs
        features = self.feature_net(policy_input)
        action_mean = self.action_mean(features)
        action_log_std = torch.clamp(self.action_log_std(features), min=-10, max=2)
        action_dist = Normal(action_mean, torch.exp(action_log_std))
        return action_dist, self.value_head(features)

    def evaluate_actions(self, obs, goal, actions):
        action_dist, value = self._distribution_value(obs, goal)
        actions = torch.as_tensor(actions, dtype=obs.dtype, device=obs.device)
        if actions.shape != action_dist.loc.shape:
            raise ValueError("stored manifold action shape does not match policy output")
        return (
            action_dist.log_prob(actions).sum(dim=-1),
            action_dist.entropy().sum(dim=-1),
            value,
        )

    def forward(self, obs, goal=None, deterministic=False):
        """
        前向传播
        
        参数:
            obs: 观测 [batch_size, obs_dim]
            goal: 目标状态 [batch_size, goal_dim]
            deterministic: 是否使用确定性策略
            
        返回:
            action: 动作 [batch_size, action_dim]
            action_logprob: 动作对数概率 [batch_size]
            value: 状态价值 [batch_size, 1]
            action_dist: 动作分布
        """
        action_dist, value = self._distribution_value(obs, goal)
        
        # 采样动作
        if deterministic:
            action = action_dist.mean
        else:
            action = action_dist.sample()
        
        # 计算对数概率
        action_logprob = action_dist.log_prob(action).sum(dim=-1)
        
        return action, action_logprob, value, action_dist

class GoalGenerator(nn.Module):
    """
    目标生成器：从VAE潜空间采样目标
    """
    def __init__(self, vae_model, goal_strategy='random', curriculum_config=None):
        super(GoalGenerator, self).__init__()
        
        self.vae_model = vae_model
        self.goal_strategy = goal_strategy
        self.curriculum_config = curriculum_config or {}
        
        # 目标难度课程
        self.current_difficulty = 0.0  # [0, 1]
        self.difficulty_update_steps = 0
        
        main_logger.info(f"目标生成器初始化: 策略={goal_strategy}")
    
    def sample_goals(self, batch_size, device, current_states=None):
        """
        采样目标状态
        
        参数:
            batch_size: 批大小
            device: 设备
            current_states: 当前状态（用于相对目标生成）
            
        返回:
            goals: 目标状态 [batch_size, state_dim]
            goal_info: 目标信息字典
        """
        if self.goal_strategy == 'random':
            # 从VAE先验分布随机采样
            goals, latent_goals = self.vae_model.sample_from_latent(batch_size, device)
            
        elif self.goal_strategy == 'curriculum':
            # 课程学习：逐渐增加目标难度
            goals, latent_goals = self._sample_curriculum_goals(batch_size, device, current_states)
            
        elif self.goal_strategy == 'adaptive':
            # 自适应采样：基于当前成功率调整目标分布
            goals, latent_goals = self._sample_adaptive_goals(batch_size, device, current_states)
            
        else:
            raise ValueError(f"未知的目标策略: {self.goal_strategy}")
        
        goal_info = {
            'strategy': self.goal_strategy,
            'difficulty': self.current_difficulty,
            'latent_goals': latent_goals
        }
        
        return goals, goal_info
    
    def _sample_curriculum_goals(self, batch_size, device, current_states):
        """课程学习目标采样"""
        # 简化版课程：根据难度调整采样范围
        if self.current_difficulty < 0.3:
            # 简单目标：在当前状态附近采样
            if current_states is not None:
                mu, _ = self.vae_model.encode(current_states)
                # 在当前潜变量附近采样
                noise_scale = 0.5
                latent_goals = mu + torch.randn_like(mu) * noise_scale
                goals = self.vae_model.decode(latent_goals)
            else:
                goals, latent_goals = self.vae_model.sample_from_latent(batch_size, device)
        else:
            # 困难目标：随机采样
            goals, latent_goals = self.vae_model.sample_from_latent(batch_size, device)
        
        return goals, latent_goals
    
    def _sample_adaptive_goals(self, batch_size, device, current_states):
        """自适应目标采样"""
        # 简化版：目前与随机采样相同
        return self.vae_model.sample_from_latent(batch_size, device)
    
    def update_difficulty(self, success_rate, step):
        """更新目标难度"""
        self.difficulty_update_steps += 1
        
        # 基于成功率调整难度
        target_success_rate = 0.3  # 目标成功率
        
        if success_rate > target_success_rate + 0.1:
            # 成功率过高，增加难度
            self.current_difficulty = min(1.0, self.current_difficulty + 0.01)
        elif success_rate < target_success_rate - 0.1:
            # 成功率过低，降低难度
            self.current_difficulty = max(0.0, self.current_difficulty - 0.01)
        
        # 记录到日志
        if self.difficulty_update_steps % 100 == 0:
            main_logger.info(f"目标难度更新: {self.current_difficulty:.3f}, "
                           f"当前成功率: {success_rate:.3f}")

class ManifoldHMASDAgent:
    """
    基于流形的目标导向HMASD代理
    """
    def __init__(self, config, vae_model_path, log_dir='logs/manifold_hmasd', device=None):
        """
        初始化代理
        
        参数:
            config: 配置对象
            vae_model_path: 训练好的VAE模型路径
            log_dir: TensorBoard日志目录
            device: 计算设备
        """
        self.config = config
        self.device = device if device is not None else torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
        
        # 确保环境维度已设置
        assert config.state_dim is not None, "必须先设置state_dim"
        assert config.obs_dim is not None, "必须先设置obs_dim"
        
        # 初始化TensorBoard
        self.log_dir = log_dir
        os.makedirs(log_dir, exist_ok=True)
        self.writer = SummaryWriter(log_dir)
        self.global_step = 0
        
        # 加载VAE模型
        self.vae_model = self._load_vae_model(vae_model_path)
        self.vae_model.eval()  # 训练期间VAE保持评估模式
        
        # 创建目标生成器
        self.goal_generator = GoalGenerator(
            vae_model=self.vae_model,
            goal_strategy='random'  # 初期使用随机策略
        )
        
        # 创建目标导向策略网络
        self.policy = GoalConditionedPolicy(
            obs_dim=config.obs_dim,
            goal_dim=config.state_dim,  # 目标是全局状态
            action_dim=config.action_dim,
            hidden_dim=config.hidden_size,
            use_goal_conditioning=True
        ).to(self.device)
        
        # 创建优化器
        self.policy_optimizer = Adam(
            self.policy.parameters(),
            lr=config.lr_discoverer,
            weight_decay=config.weight_decay
        )
        
        # 创建HER经验回放缓冲区
        self.replay_buffer = create_manifold_her_buffer(
            capacity=config.buffer_size,
            vae_model=self.vae_model,
            her_strategy='future',
            her_k=4,
            distance_threshold=0.1,
            relabel_seed=int(getattr(
                config, 'manifold_her_relabel_seed', int(getattr(config, 'seed', 0)) + 2701
            )),
            sample_seed=int(getattr(
                config, 'manifold_her_sample_seed', int(getattr(config, 'seed', 0)) + 2702
            )),
        )
        
        # 当前目标和episode状态
        self.current_goals = {}  # 各环境的当前目标
        self.episode_starts = {}  # 各环境的episode开始标志
        self._episode_ids = {}
        self._episode_timesteps = {}
        self._collection_tokens = {}
        self._collection_frontiers = {}
        self._collection_token_counter = 0
        
        # 训练统计
        self.training_info = {
            'policy_loss': [],
            'value_loss': [],
            'success_rate': [],
            'episode_rewards': [],
            'goal_distances': [],
            'reconstruction_errors': []
        }
        
        main_logger.info(f"ManifoldHMASD代理初始化完成，设备: {self.device}")
    
    def _load_vae_model(self, vae_model_path):
        """加载训练好的VAE模型"""
        if not os.path.exists(vae_model_path):
            raise FileNotFoundError(f"VAE模型文件不存在: {vae_model_path}")
        
        checkpoint = torch.load(vae_model_path, map_location=self.device)
        
        # 创建VAE模型
        model_config = checkpoint['model_config']
        vae_model = StateManifoldVAE(
            state_dim=model_config['state_dim'],
            latent_dim=model_config['latent_dim'],
            hidden_dims=model_config['hidden_dims']
        ).to(self.device)
        
        # 加载权重
        vae_model.load_state_dict(checkpoint['model_state_dict'])
        
        # 保存标准化参数
        self.state_mean = checkpoint['normalization']['state_mean'].to(self.device)
        self.state_std = checkpoint['normalization']['state_std'].to(self.device)
        
        main_logger.info(f"VAE模型加载成功: {vae_model_path}")
        main_logger.info(f"模型配置: {model_config}")
        
        return vae_model
    
    def normalize_state(self, state):
        """标准化状态（与VAE训练时一致）"""
        state_tensor = torch.tensor(state, dtype=torch.float32, device=self.device)
        if state_tensor.dim() == 1:
            state_tensor = state_tensor.unsqueeze(0)
        
        normalized = (state_tensor - self.state_mean) / self.state_std
        return normalized
    
    def denormalize_state(self, normalized_state):
        """反标准化状态"""
        return normalized_state * self.state_std + self.state_mean
    
    def step(self, observations, global_state, env_id=0, episode_step=0):
        """
        执行一个环境步骤
        
        参数:
            observations: 所有智能体的观测 [n_agents, obs_dim]
            global_state: 全局状态 [state_dim]
            env_id: 环境ID
            episode_step: 当前episode步数
            
        返回:
            actions: 所有智能体的动作 [n_agents, action_dim]
            info: 额外信息
        """
        if env_id in self._collection_frontiers:
            raise ValueError(f"environment {env_id} has an unconsumed manifold collection token")
        # 检查是否需要生成新目标（episode开始）
        if env_id not in self.current_goals or episode_step == 0:
            self._generate_new_goal(global_state, env_id)
            self.episode_starts[env_id] = True
        else:
            self.episode_starts[env_id] = False
        
        # 获取当前目标
        current_goal = self.current_goals[env_id]
        
        # 为所有智能体选择动作
        actions, action_logprobs = self._select_actions(observations, current_goal)
        token_id = f"manifold-collection:{self._collection_token_counter}"
        self._collection_token_counter += 1
        self._collection_tokens[token_id] = clone_replay_data({
            'env_id': env_id,
            'episode_id': self._episode_ids[env_id],
            'timestep': self._episode_timesteps[env_id],
            'state': global_state,
            'observations': observations,
            'goal': current_goal,
            'actions': actions,
            'old_action_logprobs': action_logprobs,
        })
        self._collection_frontiers[env_id] = token_id
        
        info = {
            'goal': current_goal.detach().cpu().numpy().copy(),
            'action_logprobs': clone_replay_data(action_logprobs),
            'episode_start': self.episode_starts[env_id],
            'env_id': env_id,
            'collection_token': token_id,
        }
        
        return clone_replay_data(actions), info

    @staticmethod
    def _collection_values_equal(left, right):
        if torch.is_tensor(left):
            left = left.detach().cpu().numpy()
        if torch.is_tensor(right):
            right = right.detach().cpu().numpy()
        return np.array_equal(np.asarray(left), np.asarray(right))

    def _validate_collection_token(self, state, observations, actions, info, env_id):
        token_id = info.get('collection_token')
        if token_id is None or token_id not in self._collection_tokens:
            raise ValueError("missing, stale, or reused manifold collection token")
        token = self._collection_tokens[token_id]
        if (
            token['env_id'] != env_id
            or info.get('env_id', env_id) != env_id
            or self._collection_frontiers.get(env_id) != token_id
            or self._episode_ids.get(env_id) != token['episode_id']
            or self._episode_timesteps.get(env_id) != token['timestep']
        ):
            raise ValueError("manifold collection token is not the trajectory frontier")
        comparisons = (
            ('state', state, token['state']),
            ('observation', observations, token['observations']),
            ('action', actions, token['actions']),
            ('goal', info.get('goal'), token['goal']),
            ('old log-probability', info.get('action_logprobs'), token['old_action_logprobs']),
        )
        for name, supplied, collected in comparisons:
            if supplied is None or not self._collection_values_equal(supplied, collected):
                raise ValueError(
                    f"manifold stored {name} does not match exact collection input"
                )
        return token_id, token
    
    def _generate_new_goal(self, global_state, env_id):
        """为指定环境生成新目标"""
        # 标准化当前状态
        current_state_normalized = self.normalize_state(global_state)
        
        # 生成目标
        goals, goal_info = self.goal_generator.sample_goals(
            batch_size=1,
            device=self.device,
            current_states=current_state_normalized
        )
        
        # 反标准化目标（用于环境交互）
        goal_denormalized = self.denormalize_state(goals[0])
        
        self.current_goals[env_id] = goal_denormalized
        self._episode_ids[env_id] = self._episode_ids.get(env_id, -1) + 1
        self._episode_timesteps[env_id] = 0
        
        # 记录目标信息
        main_logger.debug(f"环境{env_id}生成新目标，难度: {goal_info['difficulty']:.3f}")
    
    def _select_actions(self, observations, goal, deterministic=False):
        """为所有智能体选择动作"""
        n_agents = observations.shape[0]
        
        # 将目标扩展到所有智能体
        goals_expanded = goal.unsqueeze(0).expand(n_agents, -1)
        
        # 转换为张量
        obs_tensor = torch.FloatTensor(observations).to(self.device)
        
        with torch.no_grad():
            actions, action_logprobs, values, action_dist = self.policy(
                obs_tensor, goals_expanded, deterministic
            )
        
        return actions.cpu().numpy(), action_logprobs.cpu().numpy()
    
    def store_transition(self, state, next_state, observations, next_observations, actions, reward,
                        done, info, env_id=0):
        """
        存储环境交互经验
        
        参数:
            state: 当前状态
            next_state: 下一状态
            observations: 观测
            actions: 动作
            reward: 原始环境奖励
            done: 是否结束
            info: 额外信息
            env_id: 环境ID
        """
        token_id, collection = self._validate_collection_token(
            state, observations, actions, info, env_id
        )
        goal = self.current_goals.get(env_id)
        if goal is None or not self._collection_values_equal(goal, collection['goal']):
            raise ValueError("manifold current goal does not match collection frontier")
        next_state_shape = tuple(next_state.shape) if hasattr(next_state, 'shape') else np.asarray(next_state).shape
        state_shape = tuple(collection['state'].shape) if hasattr(collection['state'], 'shape') else np.asarray(collection['state']).shape
        next_observation_shape = tuple(next_observations.shape) if hasattr(next_observations, 'shape') else np.asarray(next_observations).shape
        observation_shape = tuple(collection['observations'].shape) if hasattr(collection['observations'], 'shape') else np.asarray(collection['observations']).shape
        if next_state_shape != state_shape:
            raise ValueError("manifold next-state shape does not match collection input")
        if next_observation_shape != observation_shape:
            raise ValueError("manifold next-observation shape does not match collection input")
        del self._collection_tokens[token_id]
        del self._collection_frontiers[env_id]

        state = collection['state']
        observations = collection['observations']
        actions = collection['actions']
        goal = collection['goal']
        old_action_logprobs = collection['old_action_logprobs']
        next_state = clone_replay_data(next_state)
        next_observations = clone_replay_data(next_observations)
        
        # 计算目标导向奖励（基于流形距离）
        goal_array = goal.detach().cpu().numpy().copy() if torch.is_tensor(goal) else clone_replay_data(goal)
        goal_reward = self._compute_goal_reward(next_state, goal_array)
        
        # 存储到HER缓冲区
        trajectory_id = f"manifold:{env_id}:{self._episode_ids[env_id]}"
        timestep = self._episode_timesteps.get(env_id)
        if timestep is None:
            raise ValueError("manifold trajectory has no initialized timestep")
        self.replay_buffer.store_transition(
            state=state,
            action=actions,  # 这里假设actions是所有智能体的动作
            reward=goal_reward,
            next_state=next_state,
            done=done,
            goal=goal_array,
            info={'env_reward': clone_replay_data(reward)},
            trajectory_id=trajectory_id,
            timestep=timestep,
            observation=observations,
            next_observation=next_observations,
            old_action_logprob=old_action_logprobs,
        )
        self._episode_timesteps[env_id] = timestep + 1
        
        # 如果episode结束，处理HER
        if done:
            self.replay_buffer.store_episode(
                trajectory_id=trajectory_id,
                value_function=self._trajectory_values,
                action_logprob_function=self._trajectory_action_logprobs,
                gamma=self.config.gamma,
                gae_lambda=self.config.gae_lambda,
            )
            
            # 重置环境状态
            if env_id in self.current_goals:
                del self.current_goals[env_id]
            if env_id in self.episode_starts:
                del self.episode_starts[env_id]
            self._episode_timesteps.pop(env_id, None)

    def _trajectory_values(self, observations, goals):
        observations_tensor = torch.as_tensor(
            np.asarray(observations), dtype=torch.float32, device=self.device
        )
        goals_tensor = torch.as_tensor(
            np.asarray(goals), dtype=torch.float32, device=self.device
        )
        if observations_tensor.ndim != 3:
            raise ValueError("manifold policy observations must have [time,agent,obs] shape")
        time_steps, n_agents, obs_dim = observations_tensor.shape
        expanded_goals = goals_tensor.unsqueeze(1).expand(-1, n_agents, -1)
        with torch.no_grad():
            _, _, values, _ = self.policy(
                observations_tensor.reshape(time_steps * n_agents, obs_dim),
                expanded_goals.reshape(time_steps * n_agents, -1),
                deterministic=True,
            )
        return values.reshape(time_steps, n_agents).detach().cpu()

    def _trajectory_action_logprobs(self, observations, goals, actions):
        observations_tensor = torch.as_tensor(
            np.asarray(observations), dtype=torch.float32, device=self.device
        )
        actions_tensor = torch.as_tensor(
            np.asarray(actions), dtype=torch.float32, device=self.device
        )
        goals_tensor = torch.as_tensor(
            np.asarray(goals), dtype=torch.float32, device=self.device
        )
        if observations_tensor.ndim != 3 or actions_tensor.ndim != 3:
            raise ValueError("manifold replay policy inputs must have [time,agent,*] shape")
        time_steps, n_agents, obs_dim = observations_tensor.shape
        if actions_tensor.shape[:2] != (time_steps, n_agents):
            raise ValueError("manifold replay actions do not match observation trajectory")
        expanded_goals = goals_tensor.unsqueeze(1).expand(-1, n_agents, -1)
        with torch.no_grad():
            logprobs, _entropy, _values = self.policy.evaluate_actions(
                observations_tensor.reshape(time_steps * n_agents, obs_dim),
                expanded_goals.reshape(time_steps * n_agents, -1),
                actions_tensor.reshape(time_steps * n_agents, -1),
            )
        return logprobs.reshape(time_steps, n_agents).detach().cpu()
    
    def _compute_goal_reward(self, achieved_state, goal_state):
        """
        计算基于流形的目标奖励
        
        参数:
            achieved_state: 实际达到的状态
            goal_state: 目标状态
            
        返回:
            reward: 目标奖励
        """
        # 标准化状态
        achieved_normalized = self.normalize_state(achieved_state)
        goal_normalized = self.normalize_state(goal_state)
        
        with torch.no_grad():
            # 在潜空间中计算距离
            mu_achieved, _ = self.vae_model.encode(achieved_normalized)
            mu_goal, _ = self.vae_model.encode(goal_normalized)
            
            # 欧几里得距离
            distance = torch.norm(mu_achieved - mu_goal, dim=1)
            
            # 转换为奖励（距离越小奖励越高）
            reward = -distance.item()
        
        return reward
    
    def update(self):
        """更新策略网络"""
        # Values for original and HER-relabeled segments are frozen together at
        # trajectory finalization.  Do not change the policy while any segment
        # whose GAE has not yet been frozen is still being collected.
        if self.replay_buffer.has_pending_trajectories:
            return {}
        if len(self.replay_buffer) < self.config.batch_size:
            return {}
        
        # 从HER缓冲区采样数据
        batch_data = self.replay_buffer.sample_tensors(self.config.batch_size, self.device)
        if batch_data is None:
            return {}
        
        (
            states,
            actions,
            rewards,
            next_states,
            dones,
            goals,
            advantages,
            returns,
            observations,
            _next_observations,
            old_action_logprobs,
            actor_masks,
        ) = batch_data
        batch_size, n_agents, obs_dim = observations.shape
        flat_observations = observations.reshape(batch_size * n_agents, obs_dim)
        flat_actions = actions.reshape(batch_size * n_agents, -1)
        flat_goals = goals.unsqueeze(1).expand(-1, n_agents, -1).reshape(
            batch_size * n_agents, -1
        )
        flat_old_logprobs = old_action_logprobs.reshape(-1)
        flat_actor_masks = actor_masks.unsqueeze(1).expand(-1, n_agents).reshape(-1)
        advantages = advantages.reshape(-1)
        returns = returns.reshape(-1)

        current_logprobs, current_entropy, current_values = self.policy.evaluate_actions(
            flat_observations, flat_goals, flat_actions
        )
        
        policy_loss, entropy_loss = self._actor_objective(
            current_logprobs,
            current_entropy,
            flat_old_logprobs,
            advantages,
            flat_actor_masks,
            self.config.clip_epsilon,
        )
        
        # 价值损失
        value_loss = F.mse_loss(current_values.squeeze(-1), returns)
        
        # 总损失
        total_loss = policy_loss + 0.5 * value_loss + entropy_loss
        
        # 更新网络
        self.policy_optimizer.zero_grad()
        total_loss.backward()
        torch.nn.utils.clip_grad_norm_(self.policy.parameters(), self.config.max_grad_norm)
        self.policy_optimizer.step()
        
        # 记录训练信息
        self.training_info['policy_loss'].append(policy_loss.item())
        self.training_info['value_loss'].append(value_loss.item())
        
        # 计算成功率（简化）
        goal_distances = torch.norm(states - goals, dim=1)
        success_rate = (goal_distances < 0.1).float().mean().item()
        self.training_info['success_rate'].append(success_rate)
        
        # 记录到TensorBoard
        self.writer.add_scalar('Loss/Policy', policy_loss.item(), self.global_step)
        self.writer.add_scalar('Loss/Value', value_loss.item(), self.global_step)
        self.writer.add_scalar('Loss/Total', total_loss.item(), self.global_step)
        self.writer.add_scalar('Performance/SuccessRate', success_rate, self.global_step)
        
        self.global_step += 1
        
        return {
            'policy_loss': policy_loss.item(),
            'value_loss': value_loss.item(),
            'total_loss': total_loss.item(),
            'success_rate': success_rate
        }

    @staticmethod
    def _actor_objective(
        current_logprobs,
        current_entropy,
        old_logprobs,
        advantages,
        actor_mask,
        clip_epsilon,
    ):
        """Compute PPO only for rows collected under the represented goal."""
        actor_mask = torch.as_tensor(
            actor_mask, dtype=torch.bool, device=current_logprobs.device
        ).reshape(-1)
        if actor_mask.numel() != current_logprobs.numel():
            raise ValueError("manifold actor mask shape does not match replay batch")
        if not bool(actor_mask.any().item()):
            zero = current_logprobs.sum() * 0.0
            return zero, zero
        selected_advantages = advantages[actor_mask]
        selected_advantages = (
            selected_advantages - selected_advantages.mean()
        ) / (selected_advantages.std(unbiased=False) + 1e-8)
        ratio = torch.exp(
            current_logprobs[actor_mask] - old_logprobs[actor_mask]
        )
        surr1 = ratio * selected_advantages
        surr2 = torch.clamp(
            ratio, 1 - clip_epsilon, 1 + clip_epsilon
        ) * selected_advantages
        return (
            -torch.min(surr1, surr2).mean(),
            -current_entropy[actor_mask].mean() * 0.01,
        )
    
    def _checkpoint_topology(self):
        def value(name, default=None):
            if isinstance(self.config, dict):
                return self.config.get(name, default)
            return getattr(self.config, name, default)
        policy_device = _canonical_module_device(self.policy, 'manifold policy')
        if policy_device != _canonical_device_identity(self.device):
            raise ValueError(
                "manifold sampling device does not match policy parameter device"
            )
        vae_model = getattr(getattr(self, 'goal_generator', None), 'vae_model', None)
        if vae_model is not None:
            vae_device = _canonical_module_device(vae_model, 'manifold goal VAE')
            if vae_device != policy_device:
                raise ValueError(
                    "manifold goal-sampling VAE device does not match policy device"
                )
        return {
            'obs_dim': value('obs_dim', getattr(self.policy, 'obs_dim', None)),
            'state_dim': value('state_dim', getattr(self.policy, 'goal_dim', None)),
            'action_dim': value('action_dim', getattr(self.policy, 'action_dim', None)),
            'buffer_capacity': self.replay_buffer.capacity,
            'her_strategy': self.replay_buffer.her_strategy,
            'her_k': self.replay_buffer.her_k,
            'policy_device': policy_device,
        }

    def _validate_frontier_state(self, frontier):
        required = {
            'current_goals', 'episode_starts', 'episode_ids', 'episode_timesteps',
            'goal_difficulty', 'difficulty_update_steps', 'collection_tokens',
            'collection_frontiers', 'collection_token_counter',
        }
        if not isinstance(frontier, dict) or not required.issubset(frontier):
            raise ValueError("manifold checkpoint is missing strict frontier state")
        for name in ('current_goals', 'episode_starts', 'episode_ids', 'episode_timesteps'):
            if not isinstance(frontier[name], dict):
                raise ValueError(f"invalid manifold frontier container {name}")
        goal_dim = self._checkpoint_topology()['state_dim']
        for env_id, goal in frontier['current_goals'].items():
            goal_size = goal.numel() if torch.is_tensor(goal) else np.asarray(goal).size
            if goal_dim is not None and goal_size != int(goal_dim):
                raise ValueError("manifold checkpoint goal shape does not match topology")
            if env_id not in frontier['episode_ids'] or env_id not in frontier['episode_timesteps']:
                raise ValueError("manifold checkpoint goal has no trajectory frontier")
        for env_id, timestep in frontier['episode_timesteps'].items():
            if env_id not in frontier['episode_ids']:
                raise ValueError("manifold checkpoint timestep has no episode id")
            if not isinstance(timestep, (int, np.integer)) or int(timestep) < 0:
                raise ValueError("invalid manifold checkpoint episode timestep")
        if not np.isfinite(float(frontier['goal_difficulty'])):
            raise ValueError("invalid manifold goal difficulty")
        if int(frontier['difficulty_update_steps']) < 0:
            raise ValueError("invalid manifold goal difficulty counter")
        tokens = frontier['collection_tokens']
        token_frontiers = frontier['collection_frontiers']
        if not isinstance(tokens, dict) or not isinstance(token_frontiers, dict):
            raise ValueError("invalid manifold collection-token checkpoint state")
        if set(token_frontiers.values()) != set(tokens):
            raise ValueError("manifold collection tokens do not match environment frontiers")
        topology = self._checkpoint_topology()
        for env_id, token_id in token_frontiers.items():
            token = tokens[token_id]
            observation = token.get('observations')
            action = token.get('actions')
            observation_shape = tuple(observation.shape) if hasattr(observation, 'shape') else np.asarray(observation).shape
            action_shape = tuple(action.shape) if hasattr(action, 'shape') else np.asarray(action).shape
            state_size = token.get('state').numel() if torch.is_tensor(token.get('state')) else np.asarray(token.get('state')).size
            goal_size = token.get('goal').numel() if torch.is_tensor(token.get('goal')) else np.asarray(token.get('goal')).size
            logp = token.get('old_action_logprobs')
            logp_size = logp.numel() if torch.is_tensor(logp) else np.asarray(logp).size
            if (
                token.get('env_id') != env_id
                or env_id not in frontier['episode_ids']
                or token.get('episode_id') != frontier['episode_ids'][env_id]
                or token.get('timestep') != frontier['episode_timesteps'].get(env_id)
                or state_size != int(topology['state_dim'])
                or goal_size != int(topology['state_dim'])
                or len(observation_shape) != 2
                or observation_shape[-1] != int(topology['obs_dim'])
                or action_shape != (observation_shape[0], int(topology['action_dim']))
                or logp_size != observation_shape[0]
            ):
                raise ValueError("manifold collection-token shape/frontier is invalid")
        if (
            not isinstance(frontier['collection_token_counter'], (int, np.integer))
            or int(frontier['collection_token_counter']) < len(tokens)
        ):
            raise ValueError("invalid manifold collection-token counter")

    def _validate_replay_shapes(self, replay_state):
        topology = self._checkpoint_topology()
        state_dim = int(topology['state_dim'])
        obs_dim = int(topology['obs_dim'])
        action_dim = int(topology['action_dim'])
        rows = list(replay_state.get('replay_buffer', []))
        for pending_rows in replay_state.get('episode_buffer', {}).values():
            rows.extend(pending_rows)
        for row in rows:
            for name in ('state', 'next_state', 'goal', 'achieved_goal'):
                if np.asarray(getattr(row, name)).size != state_dim:
                    raise ValueError(
                        f"manifold checkpoint {name} shape does not match topology"
                    )
            observation = np.asarray(row.observation)
            next_observation = np.asarray(row.next_observation)
            action = np.asarray(row.action)
            if (
                observation.ndim != 2 or observation.shape[-1] != obs_dim
                or next_observation.shape != observation.shape
                or action.shape != (observation.shape[0], action_dim)
                or np.asarray(row.old_action_logprob).reshape(-1).size != observation.shape[0]
            ):
                raise ValueError("manifold checkpoint policy replay shape does not match topology")
            if row.segment_id is not None:
                if (
                    np.asarray(row.advantage).reshape(-1).size != observation.shape[0]
                    or np.asarray(row.return_value).reshape(-1).size != observation.shape[0]
                ):
                    raise ValueError("manifold checkpoint frozen target shape is invalid")

    def save_model(self, path):
        """Save all state needed to continue trajectory collection exactly."""
        torch.save({
            'checkpoint_version': STRICT_CHECKPOINT_VERSION,
            'policy_state_dict': self.policy.state_dict(),
            'optimizer_state_dict': self.policy_optimizer.state_dict(),
            'config': self.config,
            'global_step': self.global_step,
            'training_info': self.training_info,
            'topology': self._checkpoint_topology(),
            'replay_buffer_state': self.replay_buffer.state_dict(),
            'frontier_state': {
                'current_goals': self.current_goals,
                'episode_starts': self.episode_starts,
                'episode_ids': self._episode_ids,
                'episode_timesteps': self._episode_timesteps,
                'goal_difficulty': self.goal_generator.current_difficulty,
                'difficulty_update_steps': self.goal_generator.difficulty_update_steps,
                'collection_tokens': self._collection_tokens,
                'collection_frontiers': self._collection_frontiers,
                'collection_token_counter': self._collection_token_counter,
            },
            'torch_sampling_rng_state': _capture_torch_sampling_rng_state(),
        }, path)
        main_logger.info(f"模型已保存到 {path}")

    def load_model(self, path):
        """Load a strict continuation checkpoint (older files are warm-start only)."""
        checkpoint = torch.load(path, map_location=self.device, weights_only=False)
        required = {
            'checkpoint_version', 'policy_state_dict', 'optimizer_state_dict', 'config',
            'global_step', 'training_info', 'topology', 'replay_buffer_state',
            'frontier_state',
            'torch_sampling_rng_state',
        }
        if not isinstance(checkpoint, dict):
            raise ValueError("manifold strict checkpoint must be a dictionary")
        missing = sorted(required.difference(checkpoint))
        if missing:
            raise ValueError(
                "manifold checkpoint missing strict state; legacy checkpoints are "
                f"warm-start only: {missing}"
            )
        extra = sorted(set(checkpoint).difference(required))
        if extra:
            raise ValueError(f"manifold strict checkpoint has unexpected keys: {extra}")
        if checkpoint['checkpoint_version'] != STRICT_CHECKPOINT_VERSION:
            raise ValueError("unsupported manifold strict checkpoint version")
        runtime_topology = self._checkpoint_topology()
        saved_device = checkpoint['topology'].get('policy_device')
        if saved_device != runtime_topology['policy_device']:
            raise ValueError(
                "manifold checkpoint policy parameter device does not match runtime device"
            )
        if checkpoint['topology'] != runtime_topology:
            raise ValueError("manifold checkpoint topology does not match runtime agent")
        self._validate_frontier_state(checkpoint['frontier_state'])
        self._validate_replay_shapes(checkpoint['replay_buffer_state'])
        _validate_torch_sampling_rng_state(checkpoint['torch_sampling_rng_state'])
        self.replay_buffer.load_state_dict(checkpoint['replay_buffer_state'])
        self.policy.load_state_dict(checkpoint['policy_state_dict'])
        self.policy_optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
        self.global_step = checkpoint['global_step']
        self.training_info = checkpoint['training_info']
        frontier = checkpoint['frontier_state']
        self.current_goals = frontier['current_goals']
        self.episode_starts = frontier['episode_starts']
        self._episode_ids = frontier['episode_ids']
        self._episode_timesteps = frontier['episode_timesteps']
        self.goal_generator.current_difficulty = float(frontier['goal_difficulty'])
        self.goal_generator.difficulty_update_steps = int(frontier['difficulty_update_steps'])
        self._collection_tokens = frontier['collection_tokens']
        self._collection_frontiers = frontier['collection_frontiers']
        self._collection_token_counter = int(frontier['collection_token_counter'])
        # Restore global Torch distribution state only after every strict load
        # above has succeeded.
        _restore_torch_sampling_rng_state(checkpoint['torch_sampling_rng_state'])
        main_logger.info(f"模型已从 {path} 加载")

    @staticmethod
    def _validate_warm_start_weights(module, state):
        if not isinstance(state, dict):
            raise ValueError("legacy manifold policy weights must be a state dictionary")
        expected = module.state_dict()
        if set(state) != set(expected):
            raise ValueError("legacy manifold policy weights have missing or extra keys")
        for name, tensor in state.items():
            if (
                not torch.is_tensor(tensor)
                or tensor.shape != expected[name].shape
                or tensor.dtype != expected[name].dtype
            ):
                raise ValueError(f"legacy manifold policy weight {name!r} is incompatible")

    def _reset_after_warm_start(self):
        def config_value(name, default):
            if isinstance(self.config, dict):
                return self.config.get(name, default)
            return getattr(self.config, name, default)
        base_seed = int(config_value('seed', 0))
        relabel_seed = int(config_value('manifold_her_relabel_seed', base_seed + 2701))
        sample_seed = int(config_value('manifold_her_sample_seed', base_seed + 2702))
        self.replay_buffer.clear()
        self.replay_buffer.set_rng_state({
            'relabel': random.Random(relabel_seed).getstate(),
            'sample': random.Random(sample_seed).getstate(),
        })
        self.current_goals = {}
        self.episode_starts = {}
        self._episode_ids = {}
        self._episode_timesteps = {}
        self._collection_tokens = {}
        self._collection_frontiers = {}
        self._collection_token_counter = 0
        self.global_step = 0
        self.training_info = {name: [] for name in self.training_info}
        self.goal_generator.current_difficulty = 0.0
        self.goal_generator.difficulty_update_steps = 0
        self.policy_optimizer.state.clear()
        torch.manual_seed(base_seed)
        if torch.cuda.is_initialized():
            torch.cuda.manual_seed_all(base_seed)

    def load_warm_start(self, path):
        """Load the historical five-key manifold checkpoint as weights only.

        Optimizer moments, counters, replay/frontier state, collection tokens,
        and sampler RNGs are deliberately reset. Strict or mixed payloads are
        rejected rather than silently downgraded.
        """
        checkpoint = torch.load(path, map_location=self.device, weights_only=False)
        if (
            not isinstance(checkpoint, dict)
            or set(checkpoint) != MANIFOLD_LEGACY_WARM_START_KEYS
        ):
            raise ValueError(
                "legacy manifold warm-start payload must contain exactly "
                "policy_state_dict, optimizer_state_dict, config, global_step, "
                "and training_info"
            )
        self._validate_warm_start_weights(self.policy, checkpoint['policy_state_dict'])
        self.policy.load_state_dict(checkpoint['policy_state_dict'], strict=True)
        self._reset_after_warm_start()
        main_logger.info(f"manifold legacy weights warm-started from {path}")
    
    def get_statistics(self):
        """获取训练统计信息"""
        buffer_stats = self.replay_buffer.get_statistics()
        
        stats = {
            'global_step': self.global_step,
            'policy_loss_mean': np.mean(self.training_info['policy_loss'][-100:]) if self.training_info['policy_loss'] else 0,
            'value_loss_mean': np.mean(self.training_info['value_loss'][-100:]) if self.training_info['value_loss'] else 0,
            'success_rate_mean': np.mean(self.training_info['success_rate'][-100:]) if self.training_info['success_rate'] else 0,
            'buffer_stats': buffer_stats,
            'goal_difficulty': self.goal_generator.current_difficulty
        }
        
        return stats
