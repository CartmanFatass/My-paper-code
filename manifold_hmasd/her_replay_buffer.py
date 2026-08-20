import torch
import numpy as np
from collections import deque
import random
import copy
from hmasd.logging import main_logger
from hmasd.utils import clone_replay_data, compute_ordered_trajectory_gae

class GoalConditionedExperience:
    """
    目标导向的经验样本
    """
    def __init__(
        self,
        state,
        action,
        reward,
        next_state,
        done,
        goal,
        achieved_goal,
        info=None,
        *,
        trajectory_id=None,
        timestep=None,
        segment_id=None,
        advantage=None,
        return_value=None,
        old_value=None,
        next_value=None,
        observation=None,
        next_observation=None,
        old_action_logprob=None,
        critic_only=False,
    ):
        self.state = clone_replay_data(state)
        self.action = clone_replay_data(action)
        self.reward = clone_replay_data(reward)
        self.next_state = clone_replay_data(next_state)
        self.done = clone_replay_data(done)
        self.goal = clone_replay_data(goal)  # 目标状态 s_g
        self.achieved_goal = clone_replay_data(achieved_goal)  # 实际达到的状态
        self.info = clone_replay_data(info or {})
        self.trajectory_id = clone_replay_data(trajectory_id)
        self.timestep = clone_replay_data(timestep)
        self.segment_id = clone_replay_data(segment_id)
        self.advantage = clone_replay_data(advantage)
        self.return_value = clone_replay_data(return_value)
        self.old_value = clone_replay_data(old_value)
        self.next_value = clone_replay_data(next_value)
        self.observation = clone_replay_data(observation)
        self.next_observation = clone_replay_data(next_observation)
        self.old_action_logprob = clone_replay_data(old_action_logprob)
        self.critic_only = bool(critic_only)

class HERReplayBuffer:
    """
    Hindsight Experience Replay (HER) 经验回放缓冲区
    
    核心思想：
    1. 存储原始的目标导向经验 (s, a, r, s', g)
    2. 对每个经验，生成额外的"事后"经验，其中目标被替换为实际达到的状态
    3. 重新计算对应的奖励，使失败的经验变成成功的经验
    """
    
    def __init__(
        self,
        capacity,
        her_strategy='future',
        her_k=4,
        reward_func=None,
        relabel_seed=0,
        sample_seed=1,
    ):
        """
        初始化HER回放缓冲区
        
        参数:
            capacity: 缓冲区容量
            her_strategy: HER策略 ('future', 'episode', 'random')
            her_k: 每个原始经验生成的HER经验数量
            reward_func: 奖励函数，用于重新计算HER经验的奖励
        """
        self.capacity = capacity
        self.her_strategy = her_strategy
        self.her_k = her_k
        self.reward_func = reward_func or self._default_reward_func
        self._relabel_rng = random.Random(int(relabel_seed))
        self._sample_rng = random.Random(int(sample_seed))
        
        # 存储完整轨迹的缓冲区
        self.episode_buffer = {}  # trajectory_id -> temporally ordered episode
        self.replay_buffer = deque(maxlen=capacity)  # 主回放缓冲区
        
        # 统计信息
        self.total_episodes = 0
        self.total_transitions = 0
        self.her_transitions = 0
        
        main_logger.info(f"创建HER回放缓冲区: capacity={capacity}, strategy={her_strategy}, k={her_k}")
    
    def _default_reward_func(self, achieved_goal, desired_goal, info=None):
        """
        默认奖励函数：基于目标距离的负奖励
        
        参数:
            achieved_goal: 实际达到的状态
            desired_goal: 期望的目标状态
            info: 额外信息
            
        返回:
            reward: 奖励值
        """
        # 计算欧几里得距离
        if isinstance(achieved_goal, torch.Tensor):
            achieved_goal = achieved_goal.detach().cpu().numpy()
        if isinstance(desired_goal, torch.Tensor):
            desired_goal = desired_goal.detach().cpu().numpy()
        
        distance = np.linalg.norm(achieved_goal - desired_goal)
        
        # 使用负距离作为奖励，可以添加阈值判断
        threshold = info.get('success_threshold', 0.1) if info else 0.1
        
        if distance <= threshold:
            reward = 0.0  # 成功到达目标
        else:
            reward = -distance  # 距离越远奖励越低
        
        return reward
    
    def store_transition(
        self,
        state,
        action,
        reward,
        next_state,
        done,
        goal,
        info=None,
        *,
        trajectory_id=None,
        timestep=None,
        observation=None,
        next_observation=None,
        old_action_logprob=None,
    ):
        """
        存储单个转移经验到episode缓冲区
        
        参数:
            state: 当前状态
            action: 执行的动作
            reward: 获得的奖励
            next_state: 下一状态
            done: 是否结束
            goal: 目标状态
            info: 额外信息
        """
        if trajectory_id is None or timestep is None:
            raise ValueError("HER transitions require trajectory_id and timestep")
        if not isinstance(timestep, (int, np.integer)) or int(timestep) < 0:
            raise ValueError("HER transition timestep must be a non-negative integer")
        timestep = int(timestep)
        rows = self.episode_buffer.setdefault(trajectory_id, [])
        if rows and timestep != rows[-1].timestep + 1:
            raise ValueError("HER trajectory timesteps must be contiguous and ordered")
        if not rows and timestep != 0:
            raise ValueError("HER trajectory must start at timestep zero")
        if rows and rows[-1].done:
            raise ValueError("cannot append after a terminal HER transition")
        if observation is None or next_observation is None or old_action_logprob is None:
            raise ValueError(
                "HER transitions require policy observation, next_observation, and old action log-prob"
            )

        achieved_goal = next_state  # 实际达到的状态就是下一状态
        
        experience = GoalConditionedExperience(
            state=clone_replay_data(state),
            action=clone_replay_data(action),
            reward=reward,
            next_state=clone_replay_data(next_state),
            done=done,
            goal=clone_replay_data(goal),
            achieved_goal=clone_replay_data(achieved_goal),
            info=clone_replay_data(info),
            trajectory_id=trajectory_id,
            timestep=timestep,
            observation=clone_replay_data(observation),
            next_observation=clone_replay_data(next_observation),
            old_action_logprob=clone_replay_data(old_action_logprob),
        )
        
        rows.append(experience)
        self.total_transitions += 1
    
    def store_episode(
        self,
        *,
        trajectory_id,
        value_function,
        action_logprob_function,
        gamma,
        gae_lambda,
    ):
        """
        在episode结束时，将episode缓冲区的经验处理并存储到主缓冲区
        """
        if trajectory_id not in self.episode_buffer:
            raise ValueError(f"unknown HER trajectory {trajectory_id!r}")
        episode = self.episode_buffer.pop(trajectory_id)
        if not episode or not episode[-1].done:
            raise ValueError("HER episode finalization requires a terminal final transition")
        variants = [("original", episode)]
        variants.extend(self._generate_her_trajectories(episode))
        for segment_id, segment in variants:
            frozen = self._freeze_segment(
                segment,
                trajectory_id=f"{trajectory_id}:{segment_id}",
                segment_id=segment_id,
                value_function=value_function,
                action_logprob_function=action_logprob_function,
                gamma=gamma,
                gae_lambda=gae_lambda,
            )
            self.replay_buffer.extend(frozen)
            if segment_id != "original":
                self.her_transitions += len(frozen)
        self.total_episodes += 1
        
        # 记录统计信息
        if self.total_episodes % 10 == 0:
            her_ratio = self.her_transitions / max(self.total_transitions, 1)
            main_logger.debug(f"HER统计: episodes={self.total_episodes}, "
                            f"total_transitions={self.total_transitions}, "
                            f"her_transitions={self.her_transitions}, "
                            f"her_ratio={her_ratio:.3f}")
    
    def _generate_her_trajectories(self, episode_experiences):
        """
        根据策略生成HER经验
        
        参数:
            episode_experiences: episode中的经验列表
            
        返回:
            her_experiences: 生成的HER经验列表
        """
        trajectories = []
        episode_length = len(episode_experiences)
        if episode_length == 0:
            return trajectories
        for anchor in range(episode_length):
            for variant in range(self.her_k):
                if self.her_strategy == 'future':
                    if anchor >= episode_length - 1:
                        continue
                    # This is the same draw made by the former row-wise HER
                    # implementation.  The selected goal is now applied to the
                    # complete continuous segment from the anchor through the
                    # strictly later goal transition.
                    goal_index = self._relabel_rng.randint(anchor + 1, episode_length - 1)
                    source = episode_experiences[anchor : goal_index + 1]
                elif self.her_strategy in {'episode', 'random'}:
                    goal_index = self._relabel_rng.randint(0, episode_length - 1)
                    source = episode_experiences[anchor:]
                else:
                    raise ValueError(f"未知的HER策略: {self.her_strategy}")
                new_goal = episode_experiences[goal_index].achieved_goal
                relabeled = [self._create_her_experience(row, new_goal) for row in source]
                if self.her_strategy == 'future':
                    # The selected future transition is included and becomes
                    # the success/terminal boundary for this relabelled segment.
                    relabeled[-1].done = True
                    relabeled[-1].info = dict(relabeled[-1].info)
                    relabeled[-1].info.update({
                        'is_success': True,
                        'success': True,
                        'goal_achieved': True,
                    })
                trajectories.append((f"her-{anchor}-{variant}", relabeled))
        return trajectories
    
    def _create_her_experience(self, original_exp, new_goal):
        """
        基于原始经验和新目标创建HER经验
        
        参数:
            original_exp: 原始经验
            new_goal: 新的目标状态
            
        返回:
            her_exp: HER经验
        """
        # 重新计算奖励
        new_reward = self.reward_func(
            original_exp.achieved_goal, 
            new_goal, 
            original_exp.info
        )
        
        # 创建新的经验
        her_exp = GoalConditionedExperience(
            state=original_exp.state,
            action=original_exp.action,
            reward=new_reward,
            next_state=original_exp.next_state,
            done=original_exp.done,
            goal=new_goal,  # 新的目标
            achieved_goal=original_exp.achieved_goal,  # 实际达到的状态不变
            info=dict(original_exp.info),
            trajectory_id=original_exp.trajectory_id,
            timestep=original_exp.timestep,
            observation=original_exp.observation,
            next_observation=original_exp.next_observation,
            old_action_logprob=original_exp.old_action_logprob,
            critic_only=True,
        )
        
        return her_exp

    def _freeze_segment(
        self,
        segment,
        *,
        trajectory_id,
        segment_id,
        value_function,
        action_logprob_function,
        gamma,
        gae_lambda,
    ):
        if not callable(value_function):
            raise TypeError("HER GAE finalization requires a callable value_function")
        if not callable(action_logprob_function):
            raise TypeError(
                "HER finalization requires a callable action_logprob_function"
            )
        observations = [row.observation for row in segment]
        next_observations = [row.next_observation for row in segment]
        goals = [row.goal for row in segment]
        actions = [row.action for row in segment]
        values = torch.as_tensor(
            value_function(observations, goals), dtype=torch.float32
        )
        next_values = torch.as_tensor(
            value_function(next_observations, goals), dtype=torch.float32
        )
        rewards = torch.as_tensor([row.reward for row in segment], dtype=torch.float32)
        dones = torch.as_tensor([row.done for row in segment], dtype=torch.float32)
        if values.ndim != 2 or next_values.shape != values.shape:
            raise ValueError("HER value_function must return [time, agent] values")
        if values.shape[0] != len(segment):
            raise ValueError("HER value_function returned the wrong trajectory length")
        # HER rows are critic-only.  Retain the genuinely collected likelihood
        # for provenance, but never synthesize an "old policy" likelihood for
        # the counterfactual goal.
        old_action_logprobs = torch.as_tensor(
            np.asarray([row.old_action_logprob for row in segment]),
            dtype=torch.float32,
        )
        if old_action_logprobs.shape != values.shape:
            raise ValueError(
                "HER action_logprob_function must return [time, agent] log-probs"
            )
        if not bool(torch.all(torch.isfinite(old_action_logprobs)).item()):
            raise ValueError("HER old action log-probs must be finite")
        advantages_by_agent = []
        returns_by_agent = []
        for agent_index in range(values.shape[1]):
            agent_advantages, agent_returns = compute_ordered_trajectory_gae(
                rewards,
                values[:, agent_index],
                next_values[:, agent_index],
                dones,
                [f"{trajectory_id}:agent-{agent_index}"] * len(segment),
                [row.timestep for row in segment],
                gamma,
                gae_lambda,
            )
            advantages_by_agent.append(agent_advantages)
            returns_by_agent.append(agent_returns)
        advantages = torch.stack(advantages_by_agent, dim=1)
        returns = torch.stack(returns_by_agent, dim=1)
        frozen = []
        for index, row in enumerate(segment):
            frozen.append(GoalConditionedExperience(
                state=row.state,
                action=row.action,
                reward=row.reward,
                next_state=row.next_state,
                done=row.done,
                goal=row.goal,
                achieved_goal=row.achieved_goal,
                info=row.info,
                trajectory_id=trajectory_id,
                timestep=row.timestep,
                segment_id=segment_id,
                advantage=advantages[index].detach().cpu().numpy(),
                return_value=returns[index].detach().cpu().numpy(),
                old_value=values[index].detach().cpu().numpy(),
                next_value=next_values[index].detach().cpu().numpy(),
                observation=row.observation,
                next_observation=row.next_observation,
                old_action_logprob=old_action_logprobs[index].detach().cpu().numpy(),
                critic_only=row.critic_only,
            ))
        return frozen
    
    def sample(self, batch_size):
        """
        从缓冲区中采样一批经验
        
        参数:
            batch_size: 批大小
            
        返回:
            batch: 采样的经验列表
        """
        if len(self.replay_buffer) < batch_size:
            # 如果缓冲区不够，返回全部
            return list(self.replay_buffer)
        
        return self._sample_rng.sample(self.replay_buffer, batch_size)

    def get_rng_state(self):
        return {
            'relabel': self._relabel_rng.getstate(),
            'sample': self._sample_rng.getstate(),
        }

    def set_rng_state(self, state):
        if not isinstance(state, dict) or set(state) != {'relabel', 'sample'}:
            raise ValueError("HER RNG state must contain exactly relabel and sample")
        relabel_rng = random.Random()
        sample_rng = random.Random()
        try:
            relabel_rng.setstate(state['relabel'])
            sample_rng.setstate(state['sample'])
        except (TypeError, ValueError) as exc:
            raise ValueError("invalid HER RNG state") from exc
        self._relabel_rng = relabel_rng
        self._sample_rng = sample_rng

    @staticmethod
    def _validate_experience(row, *, frozen):
        if not isinstance(row, GoalConditionedExperience):
            raise ValueError("HER checkpoint contains a non-experience row")
        if row.trajectory_id is None or row.timestep is None:
            raise ValueError("HER checkpoint row is missing trajectory metadata")
        if not isinstance(row.timestep, (int, np.integer)) or int(row.timestep) < 0:
            raise ValueError("HER checkpoint row has an invalid timestep")
        if row.observation is None or row.next_observation is None:
            raise ValueError("HER checkpoint row is missing policy observations")
        if row.old_action_logprob is None:
            raise ValueError("HER checkpoint row is missing collected log-probability")
        if frozen and (
            row.segment_id is None or row.advantage is None or row.return_value is None
        ):
            raise ValueError("HER replay checkpoint contains an unfrozen row")
        if not frozen and row.segment_id is not None:
            raise ValueError("pending HER checkpoint row is already segment-finalized")

    def state_dict(self):
        return {
            "version": 1,
            "topology": {
                "capacity": self.capacity,
                "her_strategy": self.her_strategy,
                "her_k": self.her_k,
            },
            "episode_buffer": copy.deepcopy(self.episode_buffer),
            "replay_buffer": copy.deepcopy(list(self.replay_buffer)),
            "total_episodes": self.total_episodes,
            "total_transitions": self.total_transitions,
            "her_transitions": self.her_transitions,
            "rng_state": self.get_rng_state(),
        }

    def load_state_dict(self, state):
        required = {
            "version", "topology", "episode_buffer", "replay_buffer",
            "total_episodes", "total_transitions", "her_transitions", "rng_state",
        }
        if not isinstance(state, dict) or not required.issubset(state):
            raise ValueError("HER checkpoint is missing strict continuation state")
        if state["version"] != 1:
            raise ValueError("unsupported HER checkpoint version")
        expected = {
            "capacity": self.capacity,
            "her_strategy": self.her_strategy,
            "her_k": self.her_k,
        }
        if state["topology"] != expected:
            raise ValueError("HER checkpoint topology does not match runtime buffer")
        pending = state["episode_buffer"]
        replay = state["replay_buffer"]
        if not isinstance(pending, dict) or not isinstance(replay, list):
            raise ValueError("invalid HER checkpoint buffer containers")
        if len(replay) > self.capacity:
            raise ValueError("HER checkpoint exceeds runtime capacity")
        for trajectory_id, rows in pending.items():
            if not isinstance(rows, list) or not rows:
                raise ValueError("HER checkpoint has an empty pending trajectory")
            for expected_timestep, row in enumerate(rows):
                self._validate_experience(row, frozen=False)
                if row.trajectory_id != trajectory_id or row.timestep != expected_timestep:
                    raise ValueError("HER checkpoint pending trajectory order is ambiguous")
                if row.done and expected_timestep != len(rows) - 1:
                    raise ValueError("HER checkpoint appends after a terminal transition")
        for row in replay:
            self._validate_experience(row, frozen=True)
        for name in ("total_episodes", "total_transitions", "her_transitions"):
            if not isinstance(state[name], (int, np.integer)) or int(state[name]) < 0:
                raise ValueError(f"invalid HER checkpoint counter {name}")
        self.set_rng_state(state["rng_state"])
        self.episode_buffer = copy.deepcopy(pending)
        self.replay_buffer = deque(copy.deepcopy(replay), maxlen=self.capacity)
        self.total_episodes = int(state["total_episodes"])
        self.total_transitions = int(state["total_transitions"])
        self.her_transitions = int(state["her_transitions"])
    
    def sample_tensors(self, batch_size, device):
        """
        采样并返回张量格式的批次数据
        
        参数:
            batch_size: 批大小
            device: 设备
            
        返回:
            states: 状态张量 [batch_size, state_dim]
            actions: 动作张量 [batch_size, action_dim]
            rewards: 奖励张量 [batch_size]
            next_states: 下一状态张量 [batch_size, state_dim]
            dones: 结束标志张量 [batch_size]
            goals: 目标张量 [batch_size, state_dim]
            advantages: 轨迹终结时冻结的GAE [batch_size]
            returns: 轨迹终结时冻结的回报目标 [batch_size]
        """
        experiences = self.sample(batch_size)
        
        if len(experiences) == 0:
            return None
        
        # 提取各个组件
        states = []
        actions = []
        rewards = []
        next_states = []
        dones = []
        goals = []
        advantages = []
        returns = []
        observations = []
        next_observations = []
        old_action_logprobs = []
        actor_masks = []
        
        for exp in experiences:
            states.append(exp.state)
            actions.append(exp.action)
            rewards.append(exp.reward)
            next_states.append(exp.next_state)
            dones.append(float(exp.done))
            goals.append(exp.goal)
            if exp.advantage is None or exp.return_value is None:
                raise ValueError("sampled HER row has not been trajectory-finalized")
            if exp.trajectory_id is None or exp.timestep is None or exp.segment_id is None:
                raise ValueError("sampled HER row is missing trajectory metadata")
            advantages.append(exp.advantage)
            returns.append(exp.return_value)
            if exp.observation is None or exp.next_observation is None or exp.old_action_logprob is None:
                raise ValueError("sampled HER row is missing exact policy replay inputs")
            observations.append(exp.observation)
            next_observations.append(exp.next_observation)
            old_action_logprobs.append(exp.old_action_logprob)
            actor_masks.append(not exp.critic_only)
        
        # 转换为张量
        def to_tensor(data):
            if isinstance(data[0], torch.Tensor):
                return torch.stack(data).to(device)
            else:
                return torch.tensor(data, dtype=torch.float32, device=device)
        
        return (
            to_tensor(states),
            to_tensor(actions),
            to_tensor(rewards),
            to_tensor(next_states),
            to_tensor(dones),
            to_tensor(goals),
            to_tensor(advantages),
            to_tensor(returns),
            to_tensor(observations),
            to_tensor(next_observations),
            to_tensor(old_action_logprobs),
            torch.as_tensor(actor_masks, dtype=torch.bool, device=device),
        )
    
    def __len__(self):
        """返回缓冲区中的经验总数"""
        return len(self.replay_buffer)

    @property
    def has_pending_trajectories(self):
        return any(bool(rows) for rows in self.episode_buffer.values())
    
    def clear(self):
        """清空缓冲区"""
        self.replay_buffer.clear()
        self.episode_buffer.clear()
        self.total_episodes = 0
        self.total_transitions = 0
        self.her_transitions = 0
        main_logger.info("HER缓冲区已清空")
    
    def get_statistics(self):
        """
        获取缓冲区统计信息
        
        返回:
            stats: 统计信息字典
        """
        her_ratio = self.her_transitions / max(self.total_transitions, 1)
        
        stats = {
            'buffer_size': len(self.replay_buffer),
            'capacity': self.capacity,
            'utilization': len(self.replay_buffer) / self.capacity,
            'total_episodes': self.total_episodes,
            'total_transitions': self.total_transitions,
            'her_transitions': self.her_transitions,
            'her_ratio': her_ratio,
            'her_strategy': self.her_strategy,
            'her_k': self.her_k,
        }
        
        return stats

class ManifoldDistanceReward:
    """
    基于流形距离的奖励函数，用于HER
    """
    def __init__(self, vae_model, distance_threshold=0.1, success_reward=0.0, 
                 distance_weight=1.0, use_latent_space=True):
        """
        初始化基于流形距离的奖励函数
        
        参数:
            vae_model: 训练好的VAE模型
            distance_threshold: 成功阈值
            success_reward: 成功时的奖励
            distance_weight: 距离权重
            use_latent_space: 是否在潜空间中计算距离
        """
        self.vae_model = vae_model
        self.distance_threshold = distance_threshold
        self.success_reward = success_reward
        self.distance_weight = distance_weight
        self.use_latent_space = use_latent_space
    
    def __call__(self, achieved_goal, desired_goal, info=None):
        """
        计算基于流形的奖励
        
        参数:
            achieved_goal: 实际达到的状态
            desired_goal: 期望的目标状态
            info: 额外信息
            
        返回:
            reward: 奖励值
        """
        # Match the VAE's parameter/buffer placement.  Creating CPU float32
        # inputs here breaks CUDA and non-default-dtype models.
        reference = next(self.vae_model.parameters(), None)
        if reference is None:
            reference = next(self.vae_model.buffers(), None)
        if reference is None:
            device, dtype = torch.device("cpu"), torch.float32
        else:
            device, dtype = reference.device, reference.dtype
        achieved_goal = torch.as_tensor(achieved_goal, device=device, dtype=dtype)
        desired_goal = torch.as_tensor(desired_goal, device=device, dtype=dtype)
        
        # 确保是二维张量
        if achieved_goal.dim() == 1:
            achieved_goal = achieved_goal.unsqueeze(0)
        if desired_goal.dim() == 1:
            desired_goal = desired_goal.unsqueeze(0)
        
        with torch.no_grad():
            if self.use_latent_space:
                # 在潜空间中计算距离
                mu_achieved, _ = self.vae_model.encode(achieved_goal)
                mu_desired, _ = self.vae_model.encode(desired_goal)
                distance = torch.norm(mu_achieved - mu_desired, dim=1)
            else:
                # 在原始状态空间中计算距离
                distance = torch.norm(achieved_goal - desired_goal, dim=1)
        
        distance = distance.item() if distance.numel() == 1 else distance.mean().item()
        
        # 计算奖励
        if distance <= self.distance_threshold:
            reward = self.success_reward
        else:
            reward = -self.distance_weight * distance
        
        return reward

def create_manifold_her_buffer(capacity, vae_model, her_strategy='future', 
                              her_k=4, distance_threshold=0.1,
                              relabel_seed=0, sample_seed=1):
    """
    创建使用流形距离的HER缓冲区
    
    参数:
        capacity: 缓冲区容量
        vae_model: VAE模型
        her_strategy: HER策略
        her_k: HER经验数量
        distance_threshold: 距离阈值
        
    返回:
        buffer: HER缓冲区
    """
    reward_func = ManifoldDistanceReward(
        vae_model=vae_model,
        distance_threshold=distance_threshold,
        use_latent_space=True  # 在潜空间中计算距离更合理
    )
    
    buffer = HERReplayBuffer(
        capacity=capacity,
        her_strategy=her_strategy,
        her_k=her_k,
        reward_func=reward_func,
        relabel_seed=relabel_seed,
        sample_seed=sample_seed,
    )
    
    return buffer
