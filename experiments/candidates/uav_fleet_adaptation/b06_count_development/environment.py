"""Direction-local native N and explicitly paired exogenous initial layouts."""
import numpy as np

from .controllers import fleet_count


def initial_layout(world, layout_root):
    users = np.random.default_rng(np.random.SeedSequence(
        [int(layout_root), int(world), 1])).uniform(0, 1000, size=(50, 2))
    seven = np.random.default_rng(np.random.SeedSequence(
        [int(layout_root), int(world), 2])).uniform(
            low=[0, 0, 50], high=[1000, 1000, 150], size=(7, 3))
    return users, seven


def make_real(n, seed, *, base_class=None, adapter_class=None):
    n = fleet_count(n)
    if base_class is None:
        from envs.pettingzoo.uav_env import MultiUAVEnv
        base_class = MultiUAVEnv
    if adapter_class is None:
        from envs.pettingzoo.env_adapter import ParallelToArrayAdapter
        adapter_class = ParallelToArrayAdapter
    base = base_class(n_uavs=n, n_users=50, area_size=1000,
                      height_range=(50, 150), max_speed=30, time_step=1.,
                      max_steps=256, user_distribution="uniform",
                      channel_model="free_space", render_mode=None, seed=seed,
                      max_observed_users=20, max_observed_uavs=10,
                      use_shadowing=False, paper_reward=False, use_fdma=False,
                      bandwidth=20e6, ground_bs_tx_power=30,
                      step_path_loss_cache=True, channel_backend="vectorized")
    return adapter_class(base, seed=seed)


def reset_layout(env, world, protocol, counts):
    """Discard native reset, then charge/perform one fresh channel/observation rebuild."""
    n = fleet_count(env.n_uavs)
    slots = n * (50 + n)
    counts["explicit_reset_calls"] += 1
    env.reset(seed=int(world))
    counts["explicit_resets"] += 1
    counts["native_dense_slots"] += slots
    users, seven = initial_layout(world, protocol.layout_root)
    base = env.env
    base.user_positions = users.copy()
    base.uav_positions = seven[:n].copy()
    if base.current_step != 0:
        raise AssertionError("native reset did not reset time")
    base._begin_path_loss_step()
    counts["layout_refresh_calls"] += 1
    base._update_channel_state()
    counts["layout_refreshes"] += 1
    counts["native_dense_slots"] += slots
    if not base._vector_channel_state_is_current():
        raise AssertionError("layout refresh left stale physical channel state")
    observations = {agent: base._get_observation(agent) for agent in base.agents}
    obs = env._dict_to_array(observations)
    info = dict(state=env._state_array(), state_info=env.get_current_state())
    if not np.array_equal(info["state_info"]["uav_positions"], seven[:n]) or not np.array_equal(
            info["state_info"]["user_positions"], users):
        raise AssertionError("adapter state differs from the selected layout")
    return obs, info, seven
