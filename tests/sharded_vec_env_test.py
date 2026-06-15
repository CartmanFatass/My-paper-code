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
