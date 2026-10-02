"""Admitted per-process native accounting, state recording, and owned straight-line executor."""
from __future__ import annotations

import hashlib
import time

from .evidence import Trace, encoded, plain

SERIES = ("contract_reward", "coverage_backhauled", "frontend_capacity_with_path_mbps",
          "mean_relays_per_routed_uav")


class Native:
    def __init__(self, bill):
        # Only constructed after the admitted parent or its checked callable child context.
        from experiments.candidates.coupled_host_joint_skills_stage1 import host, planner
        self.host, self.p, self.bill = host, planner, bill
        self.old = []
        self.query_trace = None

    def __enter__(self):
        def replace(obj, attr, counter, completed):
            original = getattr(obj, attr)
            def counted(*args, **kwargs):
                self.bill.charge(counter)
                result = original(*args, **kwargs)
                self.bill.charge(completed)
                if counter == "static_calls" and self.query_trace is not None:
                    self.query_trace.write({"positions_xyz": args[1], "allow_a2a": kwargs.get("allow_a2a", True),
                                            "info": result})
                return result
            self.old.append((obj, attr, original, attr in vars(obj)))
            setattr(obj, attr, counted)
        cls = self.host.CoupledRelayHost
        replace(cls, "reset", "resets", "resets_completed")
        replace(cls, "step", "native_steps", "native_completed")
        replace(cls, "_update_channel_state", "radio_refresh_calls", "radio_refresh_completed")
        replace(cls, "_compute_reward", "reward_calls", "reward_completed")
        replace(cls, "_compute_routing_paths", "routing_calls", "routing_completed")
        replace(cls, "_update_uav_connections", "link_update_calls", "link_update_completed")
        replace(cls, "_compute_uav_frontend_capacity", "frontend_capacity_calls", "frontend_capacity_completed")
        for attr in ("_compute_path_loss_matrix", "_compute_uav_path_loss_matrix"):
            replace(cls, attr, "path_loss_matrix_calls", "path_loss_matrix_completed")
        for attr in ("_compute_sinr", "_compute_uav_to_uav_sinr", "_compute_uav_to_bs_sinr"):
            replace(cls, attr, "scalar_sinr_calls", "scalar_sinr_completed")
        replace(self.host, "make_host", "hosts", "hosts_completed")
        replace(self.host, "static_evaluate", "static_calls", "static_completed")
        self.old.append((self.p, "static_evaluate", self.p.static_evaluate, True))
        self.p.static_evaluate = self.host.static_evaluate
        replace(self.p, "assign_targets", "matching_calls", "matching_completed")
        return self

    def __exit__(self, *exc):
        for obj, attr, original, owned in reversed(self.old):
            if owned:
                setattr(obj, attr, original)
            else:
                delattr(obj, attr)


def rng_identity(env):
    return hashlib.sha256(encoded(env.np_random.get_state())).hexdigest()


def state(env):
    # Includes the quantities independently refreshed by each paid reader static call.
    import numpy as np
    connections = np.asarray(env.connections, dtype=bool)
    association = np.where(connections.any(axis=0), connections.argmax(axis=0), -1)
    routed = np.asarray([i in env.routing_paths for i in range(6)])
    return plain({"positions_xyz": env.uav_positions, "current_step": env.current_step,
                  "user_association": association,
                  "backhauled_users_mask": (connections & routed[:, None]).any(axis=0),
                  "connections": connections, "uav_connections": env.uav_connections,
                  "uav_bs_connections": env.uav_bs_connections, "routing_paths": env.routing_paths,
                  "reward_info": env.reward_info})


def reset_identity(env, decision):
    import numpy as np
    env.a2a_enabled = True
    env.reset(seed=int(env.world_seed))
    if (not np.array_equal(env.uav_positions, decision["initial_positions_xyz"])
            or not np.array_equal(env.user_positions, decision["user_positions_xy"])
            or not np.array_equal(env.ground_bs_positions[0], decision["bs_xyz"])
            or env.current_step != 0 or not np.asarray(env._transmitter_mask).all()
            or env.action_clip_events_episode != 0):
        raise AssertionError("search-to-flight full world reset identity mismatch")
    # Reset refreshes routing after access association; recompute the host reward for t=0.
    env._compute_reward()
    return {"native_rng_sha256": rng_identity(env), "agents": list(env.agents),
            "transmitter_mask": plain(env._transmitter_mask), "state": state(env)}


def actions(positions, assigned):
    """Owned implementation checked against original whole episodes, not used as reader proof."""
    import numpy as np
    delta = np.asarray(assigned, dtype=np.float64) - positions
    distance = np.linalg.norm(delta, axis=1)
    action = np.zeros((6, 3), dtype=np.float64)
    for i in range(6):
        if distance[i] <= 1e-6:
            continue
        action[i] = delta[i] / (30.0 if distance[i] <= 30.0 else distance[i])
    norms = np.linalg.norm(action, axis=1)
    over = norms > 1
    action[over] /= norms[over][:, None]
    return action, distance


def execute(env, decision, trace_path, bill):
    import numpy as np
    started = time.perf_counter()
    reset = reset_identity(env, decision)
    assigned = np.asarray(decision["assigned_targets_xyz"], dtype=np.float64)
    trace = Trace(trace_path, bill)
    values = {k: [] for k in SERIES}
    changes, losses, arrival = [], [], None
    previous = reset["state"]
    try:
        trace.write({"type": "initial", "world": env.world_seed, "arm": decision["arm"],
                     "reset": reset, "assigned_targets_xyz": assigned,
                     "target_permutation": decision["target_permutation"]})
        for t in range(500):
            action, distance = actions(env.uav_positions, assigned)
            if arrival is None and np.all(distance <= 1e-6):
                arrival = t
            action_dict = {agent: action[i] for i, agent in enumerate(env.agents)}
            _obs, rewards, terminated, truncated, _infos = env.step(action_dict)
            current = state(env)
            team = sum(float(rewards[a]) for a in env.agents)
            if not np.isclose(team, current["reward_info"]["contract_reward"], rtol=0, atol=1e-9):
                raise AssertionError("returned team reward disagrees with native contract reward")
            for k in SERIES:
                values[k].append(float(current["reward_info"][k]))
            changes.append(sum(a != b for a, b in zip(previous["user_association"], current["user_association"])))
            losses.append(sum(a and not b for a, b in zip(previous["backhauled_users_mask"], current["backhauled_users_mask"])))
            trace.write({"type": "step", "t": t, "actions": action, "state": current,
                         "rewards": rewards, "terminations": terminated, "truncations": truncated,
                         "native_rng_sha256": rng_identity(env)})
            previous = current
            if all(terminated.values()):
                if t != 499:
                    raise AssertionError("early native termination")
                break
        if len(values[SERIES[0]]) != 500 or not all(terminated.values()):
            raise AssertionError("full H500 native terminal behavior required")
        if rng_identity(env) != reset["native_rng_sha256"]:
            raise AssertionError("native result RNG advanced during deterministic free-space flight")
    finally:
        trace.close()
    gap = np.linalg.norm(env.uav_positions - assigned, axis=1)
    if arrival is None and np.all(gap <= 1e-6):
        arrival = 500
    result = {"steps": 500, "arrival_step": arrival, "final_max_distance_to_target_m": float(gap.max()),
              "series": values, "association_changes_per_step": changes, "backhaul_losses_per_step": losses,
              "association_change_count": sum(changes), "backhaul_loss_events": sum(losses),
              "native_wall_seconds_including_trace": time.perf_counter() - started,
              "reset_identity": reset}
    for k in SERIES:
        result[k + "_mean_all"] = float(np.mean(values[k]))
        result[k + "_mean_final100"] = float(np.mean(values[k][-100:]))
    return result
