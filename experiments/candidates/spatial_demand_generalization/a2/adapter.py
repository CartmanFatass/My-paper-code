"""Native Scenario 1 layouts with the published LOCAL1 state contract."""

from envs.pettingzoo.env_adapter import ParallelToArrayAdapter
from envs.pettingzoo.scenario1 import UAVBaseStationEnv
from experiments.candidates.agent_count_generalization.adapter import CountAdapter, N_USERS

FAMILIES = ("uniform", "cluster", "hotspot")


def make_envs(families, seeds, horizon):
    if len(families) != len(seeds) or not families:
        raise ValueError("one seed and family are required per lane")
    envs = []
    try:
        for family, seed in zip(families, seeds):
            if family not in FAMILIES:
                raise ValueError(f"unknown A2 family {family}")
            native = UAVBaseStationEnv(
                n_uavs=6, n_users=N_USERS, max_steps=int(horizon),
                user_distribution=family, channel_model="free_space", seed=int(seed),
            )
            envs.append(CountAdapter(ParallelToArrayAdapter(native, seed=int(seed))))
    except BaseException:
        for env in envs:
            env.close()
        raise
    return envs
