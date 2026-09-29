"""Read-only reconstruction of the native non-paper reward components."""
import math

import numpy as np


def native_components(info, min_sinr, n_users):
    global_info = info["infos_dict"]["uav_0"]["global"]
    connections = np.asarray(global_info["connections"])
    sinr = np.asarray(global_info["sinr_matrix"])
    if connections.shape != sinr.shape or connections.ndim != 2 or connections.shape[1] != n_users:
        raise ValueError("invalid native connection/SINR dimensions")
    served = int(connections.sum())
    if served != int(global_info["served_users"]):
        raise ValueError("native served-user count disagrees with connections")
    quality = float(np.clip((sinr[connections] - min_sinr) / 30, 0, 1).sum() / max(served, 1))
    service = .7 * served / n_users
    sinr_component = .3 * quality
    return dict(served_users=served, service_component=service,
                sinr_quality=quality, sinr_component=sinr_component,
                reconstructed_reward=service + sinr_component)


class MeasuredEnv:
    def __init__(self, env):
        self.env = env
        self.steps = []

    def reset(self, *args, **kwargs):
        self.steps = []
        return self.env.reset(*args, **kwargs)

    def step(self, actions):
        result = self.env.step(actions)
        info = result[-1]
        base = self.env.env
        row = native_components(info, base.min_sinr, base.n_users)
        factual = sum(float(x) for x in info["rewards_dict"].values())
        if not math.isclose(factual, row["reconstructed_reward"], rel_tol=1e-6, abs_tol=1e-7):
            raise ValueError("native reward decomposition mismatch")
        self.steps.append(row)
        return result

    def episode_metrics(self):
        if not self.steps:
            raise ValueError("episode has no factual native steps")
        fields = ("served_users", "service_component", "sinr_quality", "sinr_component")
        return {name: math.fsum(row[name] for row in self.steps) / len(self.steps)
                for name in fields}

    def close(self):
        return self.env.close()
