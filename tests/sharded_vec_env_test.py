import numpy as np
import gymnasium as gym
from gymnasium.spaces import Box

from hmasd.sharded_vec_env import ShardedSubprocVecEnv


class DummyShardedEnv(gym.Env):
    def __init__(self, rank: int):
        super().__init__()
        self.rank = rank
        self.step_count = 0
        self.state_dim = 2
        self.obs_dim = 2
        self.action_dim = 1
        self.render_mode = None
        self.observation_space = Box(low=-1000.0, high=1000.0, shape=(1, 2), dtype=np.float32)
        self.action_space = Box(low=-1.0, high=1.0, shape=(1,), dtype=np.float32)

    def _obs(self):
        return np.array([[self.rank, self.step_count]], dtype=np.float32)

    def _state(self):
        return np.array([self.rank, self.step_count], dtype=np.float32)

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        self.step_count = 0
        return self._obs(), {"state": self._state()}

    def step(self, action):
        self.step_count += 1
        obs = self._obs()
        state = self._state()
        reward = float(self.rank + self.step_count)
        done = self.step_count >= 2
        info = {
            "next_state": state,
            "coverage_ratio": 0.1 * (self.rank + 1),
            "reward_info": {
                "coverage_ratio": 0.1 * (self.rank + 1),
                "effective_connected_users": self.rank + self.step_count,
                "system_throughput_mbps": 10.0 + self.rank,
            },
        }
        return obs, reward, done, False, info


def make_dummy_env(rank):
    return lambda: DummyShardedEnv(rank)


def make_vec_env(metrics_mode="light"):
    return ShardedSubprocVecEnv(
        [make_dummy_env(0), make_dummy_env(1)],
        num_workers=2,
        envs_per_worker=1,
        metrics_mode=metrics_mode,
        start_method="spawn",
    )


class SeededShardedEnv(gym.Env):
    """Small stochastic environment that exposes every reset seed in its outputs."""

    def __init__(self, rank: int):
        super().__init__()
        self.rank = rank
        self.step_count = 0
        self.draw = 0
        self.state_dim = 3
        self.obs_dim = 3
        self.action_dim = 1
        self.render_mode = None
        self.observation_space = Box(low=-1.0e9, high=1.0e9, shape=(1, 3), dtype=np.float32)
        self.action_space = Box(low=-1.0, high=1.0, shape=(1,), dtype=np.float32)

    def _obs(self):
        return np.array([[self.rank, self.draw, self.step_count]], dtype=np.float32)

    def _state(self):
        return np.array([self.rank, self.draw, self.step_count], dtype=np.float32)

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        self.step_count = 0
        self.draw = int(self.np_random.integers(0, 1_000_000))
        return self._obs(), {"state": self._state(), "reset_seed": seed}

    def step(self, action):
        self.step_count += 1
        return self._obs(), float(self.draw), True, False, {"next_state": self._state()}


def make_seeded_sharded_env(rank):
    return lambda: SeededShardedEnv(rank)


def make_seeded_vec_env(num_workers: int, envs_per_worker: int):
    return ShardedSubprocVecEnv(
        [make_seeded_sharded_env(rank) for rank in range(3)],
        num_workers=num_workers,
        envs_per_worker=envs_per_worker,
        metrics_mode="full",
        start_method="spawn",
    )


def test_sharded_shared_state_and_terminal_buffers():
    env = make_vec_env(metrics_mode="light")
    try:
        observations = env.reset()
        np.testing.assert_allclose(observations[:, 0, :], [[0, 0], [1, 0]])
        np.testing.assert_allclose(env.get_states(), [[0, 0], [1, 0]])

        actions = np.zeros((2, 1), dtype=np.float32)
        observations, rewards, dones, infos = env.step(actions)
        np.testing.assert_allclose(observations[:, 0, :], [[0, 1], [1, 1]])
        np.testing.assert_allclose(env.get_next_states(), [[0, 1], [1, 1]])
        np.testing.assert_allclose(env.get_states(), [[0, 1], [1, 1]])
        assert not np.any(dones)
        assert np.isclose(infos[0]["reward_info"]["coverage_ratio"], 0.1)
        assert np.isclose(infos[1]["reward_info"]["system_throughput_mbps"], 11.0)
        profile = env.get_profile()
        assert profile["steps"] == 1
        assert profile["worker_wait_time"] >= 0.0
        assert profile["info_rebuild_time"] >= 0.0

        observations, rewards, dones, infos = env.step(actions)
        assert np.all(dones)
        np.testing.assert_allclose(env.get_next_states(), [[0, 2], [1, 2]])
        np.testing.assert_allclose(env.get_terminal_states(), [[0, 2], [1, 2]])
        np.testing.assert_allclose(env.get_terminal_observations()[:, 0, :], [[0, 2], [1, 2]])
        np.testing.assert_allclose(env.get_reset_states(), [[0, 0], [1, 0]])
        np.testing.assert_allclose(env.get_states(), [[0, 0], [1, 0]])
        np.testing.assert_allclose(observations[:, 0, :], [[0, 0], [1, 0]])
        np.testing.assert_allclose(infos[0]["terminal_observation"], [[0, 2]])
        np.testing.assert_allclose(infos[0]["terminal_state"], [0, 2])
        np.testing.assert_allclose(infos[0]["reset_state"], [0, 0])
    finally:
        env.close()


def test_sharded_metrics_modes():
    actions = np.zeros((2, 1), dtype=np.float32)

    light_env = make_vec_env(metrics_mode="light")
    try:
        light_env.reset()
        _, _, _, infos = light_env.step(actions)
        assert "reward_info" in infos[0]
        assert "next_state" not in infos[0]
    finally:
        light_env.close()

    full_env = make_vec_env(metrics_mode="full")
    try:
        full_env.reset()
        _, _, _, infos = full_env.step(actions)
        assert "reward_info" in infos[0]
        assert "next_state" in infos[0]
    finally:
        full_env.close()

    train_only_env = make_vec_env(metrics_mode="train_only")
    try:
        train_only_env.reset()
        _, _, _, infos = train_only_env.step(actions)
        assert infos == [{}, {}]
    finally:
        train_only_env.close()


def test_sharded_reset_seed_forwards_global_indices_and_auto_reset_progression():
    env = make_seeded_vec_env(num_workers=1, envs_per_worker=3)
    try:
        observations = env.reset(seed=101)
        assert [info["reset_seed"] for info in env.reset_infos] == [101, 102, 103]

        actions = np.zeros((3, 1), dtype=np.float32)
        first_reset_observations, _, dones, infos = env.step(actions)
        assert np.all(dones)
        assert [info["reset_info"]["reset_seed"] for info in infos] == [104, 105, 106]

        second_reset_observations, _, dones, infos = env.step(actions)
        assert np.all(dones)
        assert [info["reset_info"]["reset_seed"] for info in infos] == [107, 108, 109]
        assert not np.array_equal(observations, first_reset_observations)
        assert not np.array_equal(first_reset_observations, second_reset_observations)
    finally:
        env.close()


def test_sharded_seed_queue_is_reproducible_across_worker_sharding():
    pipe_style = make_seeded_vec_env(num_workers=3, envs_per_worker=1)
    sharded = make_seeded_vec_env(num_workers=1, envs_per_worker=3)
    try:
        assert pipe_style.seed(211) == [211, 212, 213]
        assert sharded.seed(211) == [211, 212, 213]
        np.testing.assert_array_equal(pipe_style.reset(), sharded.reset())
        assert [info["reset_seed"] for info in pipe_style.reset_infos] == [211, 212, 213]
        assert [info["reset_seed"] for info in pipe_style.reset_infos] == [
            info["reset_seed"] for info in sharded.reset_infos
        ]
        np.testing.assert_array_equal(pipe_style.get_states(), sharded.get_states())

        actions = np.zeros((3, 1), dtype=np.float32)
        for expected_seeds in ([214, 215, 216], [217, 218, 219]):
            pipe_obs, pipe_rewards, pipe_dones, pipe_infos = pipe_style.step(actions)
            sharded_obs, sharded_rewards, sharded_dones, sharded_infos = sharded.step(actions)
            np.testing.assert_array_equal(pipe_obs, sharded_obs)
            np.testing.assert_array_equal(pipe_rewards, sharded_rewards)
            np.testing.assert_array_equal(pipe_dones, sharded_dones)
            assert [info["reset_info"]["reset_seed"] for info in pipe_infos] == expected_seeds
            assert [info["reset_info"]["reset_seed"] for info in pipe_infos] == [
                info["reset_info"]["reset_seed"] for info in sharded_infos
            ]
            np.testing.assert_array_equal(pipe_style.get_next_states(), sharded.get_next_states())
            np.testing.assert_array_equal(pipe_style.get_states(), sharded.get_states())
    finally:
        pipe_style.close()
        sharded.close()
