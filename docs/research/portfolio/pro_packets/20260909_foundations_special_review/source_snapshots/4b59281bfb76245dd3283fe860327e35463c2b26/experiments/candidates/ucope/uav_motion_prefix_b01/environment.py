"""The unchanged base interface, own-information features and opening commitment."""
import numpy as np


AGENTS = tuple(f"uav_{i}" for i in range(5))


def make_real(seed, base_class=None, adapter_class=None):
    # These imports are reached only by an explicit real invocation.
    if base_class is None:
        from envs.pettingzoo.uav_env import MultiUAVEnv
        base_class = MultiUAVEnv
    if adapter_class is None:
        from envs.pettingzoo.env_adapter import ParallelToArrayAdapter
        adapter_class = ParallelToArrayAdapter
    base = base_class(n_uavs=5, n_users=50, area_size=1000,
                      height_range=(50, 150), max_speed=30, time_step=1.0,
                      max_steps=256, user_distribution="uniform",
                      channel_model="free_space", render_mode=None, seed=seed,
                      max_observed_users=20, max_observed_uavs=10,
                      use_shadowing=False, paper_reward=False, use_fdma=False,
                      bandwidth=20e6, ground_bs_tx_power=30,
                      step_path_loss_cache=True, channel_backend="vectorized")
    return adapter_class(base, seed=seed)


def actor_features(obs, last, remaining):
    return np.concatenate((np.asarray(obs, dtype=np.float32), last,
                           remaining[:, None] / 4), axis=-1).astype(np.float32)


def critic_features(state, last, remaining):
    state = np.array(state, dtype=np.float32, copy=True)
    xyz = state[:15].reshape(5, 3)
    xyz[:, :2] /= 1000
    xyz[:, 2] = (xyz[:, 2] - 50) / 100
    state[15:115] /= 1000
    commitments = np.concatenate((last, remaining[:, None] / 4), axis=1)
    return np.concatenate((state, commitments.ravel())).astype(np.float32)


def own_positions(obs):
    xyz = np.array(obs[:, :3], dtype=np.float64, copy=True)
    xyz[:, :2] *= 1000
    xyz[:, 2] = 50 + 100 * xyz[:, 2]
    return xyz


def team_reward(info):
    return sum(float(info["rewards_dict"][a]) for a in AGENTS)


def local_indices(adapter, agent):
    base = adapter.env
    users = base._local_user_entries(agent)[0][:20].copy().tolist()
    uavs = base._local_uav_entries(agent)[0][:10].copy().tolist()
    return {"local_user_indices": users, "local_uav_indices": uavs}


class HoldState:
    def __init__(self, renewal=False):
        self.renewal = renewal
        self.last = np.zeros((5, 3), dtype=np.float32)
        self.remaining = np.zeros(5, dtype=np.int64)

    def decide(self, t, sampled, durations):
        active = self.remaining == 0
        sent = self.last.copy()
        sent[active] = sampled[active]
        self.remaining[active] = durations[active] if t == 0 or self.renewal else 1
        return sent, active

    def advance(self, sent):
        self.last[:] = sent
        self.remaining = np.maximum(self.remaining - 1, 0)


class SyntheticAdapter:
    """Deterministic non-UAV fixture, with the base adapter's tuple/key layout."""
    def __init__(self, seed, horizon=8):
        self.env = self
        self.horizon = horizon
        self.index_calls = 0
        self.reset(seed)  # Mimic the base constructor's unscored reset.

    def reset(self, seed=None):
        rng = np.random.default_rng(seed)
        self.positions = rng.uniform(200, 800, (5, 3))
        self.positions[:, 2] = rng.uniform(70, 130, 5)
        self.users = rng.uniform(0, 1000, (50, 2))
        self.t = 0
        return self._obs(), {"state": self._state()}

    def _state(self):
        return np.concatenate((self.positions.ravel(), self.users.ravel(),
                               [self.t / self.horizon])).astype(np.float32)

    def _obs(self):
        obs = np.zeros((5, 104), dtype=np.float32)
        obs[:, :2] = self.positions[:, :2] / 1000
        obs[:, 2] = (self.positions[:, 2] - 50) / 100
        obs[:, 3:63] = np.tile(self.users[:20, 0] / 1000, 3)
        obs[:, -1] = self.t / self.horizon
        return obs

    def step(self, actions):
        self.positions += np.asarray(actions, dtype=np.float64) * 30
        self.positions[:, :2] = np.clip(self.positions[:, :2], 0, 1000)
        self.positions[:, 2] = np.clip(self.positions[:, 2], 50, 150)
        self.t += 1
        reward = float(.2 + .03 * np.asarray(actions).sum()
                       - .01 * np.square(actions).sum())
        info = {"next_state": self._state(),
                "rewards_dict": {a: reward / 5 for a in AGENTS},
                "infos_dict": {a: {"global": {"served_users": 7}} for a in AGENTS}}
        return self._obs(), reward / 5, self.t == self.horizon, False, info

    def _local_user_entries(self, i):
        self.index_calls += 1
        return np.arange(i, i + 25), np.ones(25)

    def _local_uav_entries(self, i):
        self.index_calls += 1
        ids = np.array([j for j in range(5) if j != i])
        return ids, np.ones(4)
