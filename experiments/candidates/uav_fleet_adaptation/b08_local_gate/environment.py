"""Original N5 reset factory, enabling only the declared transmitter setter."""
import numpy as np

from experiments.candidates.ucope.uav_motion_prefix_b01.environment import make_real as original_factory


def make_real(seed, *, base_class=None, adapter_class=None):
    if base_class is None:
        from envs.pettingzoo.uav_env import MultiUAVEnv
        base_class = MultiUAVEnv

    def masked_base(**kwargs):
        return base_class(**kwargs, enable_transmitter_mask=True)

    return original_factory(seed, base_class=masked_base, adapter_class=adapter_class)


def original_layout(world):
    rng = np.random.RandomState(int(world))
    positions = np.array([[rng.uniform(0, 1000), rng.uniform(0, 1000), rng.uniform(50, 150)]
                          for _ in range(5)], dtype=np.float64)
    users = np.array([[rng.uniform(0, 1000), rng.uniform(0, 1000)] for _ in range(50)], dtype=np.float64)
    return positions, users


def check_host(env):
    base = env.env
    fixed = dict(n_uavs=5, n_users=50, area_size=1000, max_speed=30, time_step=1.,
                 max_steps=256, user_distribution="uniform", channel_model="free_space",
                 max_observed_users=20, max_observed_uavs=10, use_shadowing=False,
                 paper_reward=False, use_fdma=False, channel_backend="vectorized",
                 enable_transmitter_mask=True, min_sinr=3., max_connections=10,
                 tx_power=23., noise_power=-80.)
    for key, value in fixed.items():
        if getattr(base, key) != value:
            raise ValueError("native host contract changed: " + key)
    if tuple(base.height_range) != (50, 150):
        raise ValueError("height range changed")
    return fixed
