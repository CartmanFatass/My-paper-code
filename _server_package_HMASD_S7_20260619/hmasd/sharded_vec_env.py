import math
import multiprocessing as mp
import time
from multiprocessing import shared_memory
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence

import numpy as np
from stable_baselines3.common.vec_env import VecEnv
from stable_baselines3.common.vec_env.subproc_vec_env import CloudpickleWrapper


SHARED_METRIC_KEYS = (
    "coverage_ratio",
    "effective_connected_users",
    "connected_users",
    "system_throughput_mbps",
    "avg_throughput_per_user_mbps",
    "rt_final_health_score",
    "load_balance_score",
    "load_balance_penalty",
    "demand_satisfaction_ratio",
    "capacity_limited_throughput_mbps",
    "relay_route_loss_ratio",
    "robustness_penalty",
    "backhaul_margin_penalty_raw",
    "min_serving_backhaul_bottleneck_mbps",
    "backhaul_outage_ratio",
    "avg_hops",
    "discovery_reward",
    "discovered_users_count",
    "weighted_discovery_reward",
    "discovery_progress",
    "served_users",
    "total_users",
    "battery_mean_ratio",
    "battery_min_ratio",
    "low_battery_uav_count",
    "depleted_uav_count",
    "charging_uav_count",
    "charging_queue_len",
    "uav_failed_count",
    "energy_penalty",
    "charge_progress_reward",
    "energy_reward_delta",
    "low_battery_distance_penalty",
    "depleted_battery_penalty",
    "charging_queue_penalty",
)

TOP_LEVEL_METRIC_KEYS = (
    "coverage_ratio",
    "served_users",
    "discovery_reward",
    "discovered_users_count",
    "discovery_progress",
    "total_users",
)


def _make_shared_array(shape, dtype):
    dtype = np.dtype(dtype)
    size = int(np.prod(shape)) * dtype.itemsize
    shm = shared_memory.SharedMemory(create=True, size=size)
    array = np.ndarray(shape, dtype=dtype, buffer=shm.buf)
    array.fill(0)
    return shm, array


def _attach_shared_array(name, shape, dtype):
    shm = shared_memory.SharedMemory(name=name)
    array = np.ndarray(shape, dtype=np.dtype(dtype), buffer=shm.buf)
    return shm, array


def _extract_scalar_metrics(info: Dict[str, Any]) -> Dict[str, float]:
    metrics: Dict[str, float] = {}
    reward_info = info.get("reward_info", {})
    if isinstance(reward_info, dict):
        for key in SHARED_METRIC_KEYS:
            value = reward_info.get(key)
            if np.isscalar(value):
                metrics[key] = float(value)

    for key in TOP_LEVEL_METRIC_KEYS:
        if key not in metrics:
            value = info.get(key)
            if np.isscalar(value):
                metrics[key] = float(value)
    return metrics


def _write_shared_metrics(info: Dict[str, Any], metric_values, metric_present):
    metric_values.fill(0.0)
    metric_present.fill(False)
    for metric_idx, key in enumerate(SHARED_METRIC_KEYS):
        value = None
        reward_info = info.get("reward_info", {})
        if isinstance(reward_info, dict) and key in reward_info:
            value = reward_info[key]
        elif key in TOP_LEVEL_METRIC_KEYS and key in info:
            value = info[key]
        if np.isscalar(value):
            metric_values[metric_idx] = float(value)
            metric_present[metric_idx] = True


def _light_info_from_metrics(metric_values, metric_present) -> Dict[str, Any]:
    reward_info = {}
    result: Dict[str, Any] = {}
    for metric_idx, key in enumerate(SHARED_METRIC_KEYS):
        if not metric_present[metric_idx]:
            continue
        value = float(metric_values[metric_idx])
        reward_info[key] = value
        if key in TOP_LEVEL_METRIC_KEYS:
            result[key] = value
    if reward_info:
        result["reward_info"] = reward_info
    return result


def _compact_info(info: Dict[str, Any], metrics_mode: str) -> Dict[str, Any]:
    if metrics_mode == "full":
        return dict(info)
    if metrics_mode == "train_only":
        return {}

    metrics = _extract_scalar_metrics(info)
    return _light_info_from_metrics(
        np.array([metrics.get(key, 0.0) for key in SHARED_METRIC_KEYS], dtype=np.float32),
        np.array([key in metrics for key in SHARED_METRIC_KEYS], dtype=np.bool_),
    )


def _worker_loop(
    worker_id: int,
    env_fns: Sequence[Callable[[], Any]],
    global_indices: Sequence[int],
    conn,
    shared_specs: Dict[str, Any],
    metrics_mode: str,
):
    envs = []
    shms = []
    try:
        envs = [env_fn.var() for env_fn in env_fns]
        obs_shm, obs = _attach_shared_array(*shared_specs["observations"])
        state_shm, states = _attach_shared_array(*shared_specs["states"])
        next_state_shm, next_states = _attach_shared_array(*shared_specs["next_states"])
        terminal_obs_shm, terminal_observations = _attach_shared_array(*shared_specs["terminal_observations"])
        terminal_state_shm, terminal_states = _attach_shared_array(*shared_specs["terminal_states"])
        reset_state_shm, reset_states = _attach_shared_array(*shared_specs["reset_states"])
        has_terminal_shm, has_terminal = _attach_shared_array(*shared_specs["has_terminal"])
        action_shm, actions = _attach_shared_array(*shared_specs["actions"])
        reward_shm, rewards = _attach_shared_array(*shared_specs["rewards"])
        done_shm, dones = _attach_shared_array(*shared_specs["dones"])
        metric_value_shm, metric_values = _attach_shared_array(*shared_specs["metric_values"])
        metric_present_shm, metric_present = _attach_shared_array(*shared_specs["metric_present"])
        shms.extend([
            obs_shm,
            state_shm,
            next_state_shm,
            terminal_obs_shm,
            terminal_state_shm,
            reset_state_shm,
            has_terminal_shm,
            action_shm,
            reward_shm,
            done_shm,
            metric_value_shm,
            metric_present_shm,
        ])

        def reset_env(local_idx: int, seed=None, reset_step_outputs: bool = True):
            env = envs[local_idx]
            reset_result = env.reset(seed=seed) if seed is not None else env.reset()
            env_obs, info = reset_result
            global_idx = global_indices[local_idx]
            obs[global_idx] = env_obs
            states[global_idx] = info.get("state", np.zeros(states.shape[1], dtype=states.dtype))
            reset_states[global_idx] = states[global_idx]
            if reset_step_outputs:
                next_states[global_idx] = states[global_idx]
                terminal_observations[global_idx] = obs[global_idx]
                terminal_states[global_idx] = states[global_idx]
                has_terminal[global_idx] = False
                rewards[global_idx] = 0.0
                dones[global_idx] = False
                metric_values[global_idx].fill(0.0)
                metric_present[global_idx].fill(False)
            return env_obs, info

        while True:
            command, payload = conn.recv()

            if command == "reset":
                return_obs = bool(payload.get("return_obs", False)) if isinstance(payload, dict) else False
                results = []
                for local_idx in range(len(envs)):
                    env_obs, info = reset_env(local_idx)
                    compact_info = _compact_info(info, metrics_mode)
                    compact_info.setdefault("state", states[global_indices[local_idx]].copy())
                    if return_obs:
                        results.append((env_obs, compact_info))
                    else:
                        results.append(compact_info)
                conn.send(("ok", results))

            elif command == "step":
                infos = []
                for local_idx, env in enumerate(envs):
                    global_idx = global_indices[local_idx]
                    has_terminal[global_idx] = False
                    step_obs, reward, terminated, truncated, info = env.step(actions[global_idx].copy())
                    done = bool(terminated or truncated)
                    actual_next_state = info.get(
                        "next_state",
                        np.zeros(next_states.shape[1], dtype=next_states.dtype),
                    )
                    next_states[global_idx] = actual_next_state
                    terminal_observations[global_idx] = step_obs
                    terminal_states[global_idx] = actual_next_state
                    rewards[global_idx] = float(reward)
                    dones[global_idx] = done
                    _write_shared_metrics(info, metric_values[global_idx], metric_present[global_idx])

                    compact_info = dict(info) if metrics_mode == "full" else {}
                    if metrics_mode == "full":
                        compact_info["next_state"] = next_states[global_idx].copy()
                    if done:
                        has_terminal[global_idx] = True
                        _, reset_info = reset_env(local_idx, reset_step_outputs=False)
                        reset_states[global_idx] = states[global_idx]
                        if metrics_mode == "full":
                            compact_info["terminal_observation"] = terminal_observations[global_idx].copy()
                            compact_info["terminal_state"] = terminal_states[global_idx].copy()
                            compact_info["reset_state"] = reset_states[global_idx].copy()
                            compact_info["reset_info"] = _compact_info(reset_info, metrics_mode)
                        elif metrics_mode == "light":
                            compact_info["reset_info"] = _compact_info(reset_info, metrics_mode)
                    else:
                        obs[global_idx] = step_obs
                        states[global_idx] = actual_next_state
                        reset_states[global_idx] = actual_next_state
                    infos.append(compact_info)
                conn.send(("ok", infos))

            elif command == "env_method":
                method_name = payload["method_name"]
                method_args = payload.get("args", ())
                method_kwargs = payload.get("kwargs", {})
                local_indices = payload.get("local_indices")
                if local_indices is None:
                    local_indices = range(len(envs))
                results = []
                for local_idx in local_indices:
                    method = getattr(envs[local_idx], method_name)
                    results.append(method(*method_args, **method_kwargs))
                conn.send(("ok", results))

            elif command == "get_attr":
                attr_name = payload["attr_name"]
                local_indices = payload.get("local_indices")
                if local_indices is None:
                    local_indices = range(len(envs))
                conn.send(("ok", [getattr(envs[local_idx], attr_name) for local_idx in local_indices]))

            elif command == "set_attr":
                attr_name = payload["attr_name"]
                value = payload["value"]
                local_indices = payload.get("local_indices")
                if local_indices is None:
                    local_indices = range(len(envs))
                for local_idx in local_indices:
                    setattr(envs[local_idx], attr_name, value)
                conn.send(("ok", None))

            elif command == "is_wrapped":
                conn.send(("ok", [False] * len(envs)))

            elif command == "close":
                for env in envs:
                    close = getattr(env, "close", None)
                    if close is not None:
                        close()
                conn.send(("ok", None))
                break

            else:
                raise RuntimeError(f"Unknown sharded env worker command: {command}")
    except Exception as exc:
        try:
            conn.send(("error", repr(exc)))
        except Exception:
            pass
    finally:
        for env in envs:
            close = getattr(env, "close", None)
            if close is not None:
                try:
                    close()
                except Exception:
                    pass
        for shm in shms:
            try:
                shm.close()
            except Exception:
                pass
        conn.close()


class ShardedSubprocVecEnv(VecEnv):
    """SB3-compatible synchronous VecEnv with multiple envs per worker process."""

    def __init__(
        self,
        env_fns: Sequence[Callable[[], Any]],
        num_workers: int,
        envs_per_worker: int,
        metrics_mode: str = "light",
        start_method: str = "spawn",
    ):
        if not env_fns:
            raise ValueError("ShardedSubprocVecEnv requires at least one environment")
        if metrics_mode not in {"light", "full", "train_only"}:
            raise ValueError(f"Unsupported metrics_mode: {metrics_mode}")

        self.num_workers = max(1, int(num_workers))
        self.envs_per_worker = max(1, int(envs_per_worker))
        self.metrics_mode = metrics_mode
        self.waiting = False
        self.closed = False
        self._actions_pending = False
        self._profile = {
            "action_copy_time": 0.0,
            "worker_wait_time": 0.0,
            "info_rebuild_time": 0.0,
            "steps": 0,
        }
        self._parent_conns = []
        self._worker_global_indices = []

        sample_env = env_fns[0]()
        observation_space = sample_env.observation_space
        action_space = sample_env.action_space
        self._initial_attr_cache = {
            "render_mode": getattr(sample_env, "render_mode", None),
        }
        self.state_dim = int(getattr(sample_env, "state_dim"))
        self.obs_dim = int(getattr(sample_env, "obs_dim"))
        self.action_dim = int(getattr(sample_env, "action_dim", action_space.shape[-1] if action_space.shape else 1))
        close = getattr(sample_env, "close", None)
        if close is not None:
            close()

        super().__init__(len(env_fns), observation_space, action_space)

        obs_shape = (self.num_envs,) + tuple(observation_space.shape)
        state_shape = (self.num_envs, self.state_dim)
        action_shape = (self.num_envs,) + tuple(action_space.shape)

        self._obs_shm, self._observations = _make_shared_array(obs_shape, observation_space.dtype)
        self._state_shm, self._states = _make_shared_array(state_shape, np.float32)
        self._next_state_shm, self._next_states = _make_shared_array(state_shape, np.float32)
        self._terminal_obs_shm, self._terminal_observations = _make_shared_array(obs_shape, observation_space.dtype)
        self._terminal_state_shm, self._terminal_states = _make_shared_array(state_shape, np.float32)
        self._reset_state_shm, self._reset_states = _make_shared_array(state_shape, np.float32)
        self._has_terminal_shm, self._has_terminal = _make_shared_array((self.num_envs,), np.bool_)
        self._action_shm, self._actions = _make_shared_array(action_shape, action_space.dtype)
        self._reward_shm, self._rewards = _make_shared_array((self.num_envs,), np.float32)
        self._done_shm, self._dones = _make_shared_array((self.num_envs,), np.bool_)
        self._metric_value_shm, self._metric_values = _make_shared_array(
            (self.num_envs, len(SHARED_METRIC_KEYS)), np.float32
        )
        self._metric_present_shm, self._metric_present = _make_shared_array(
            (self.num_envs, len(SHARED_METRIC_KEYS)), np.bool_
        )
        self._owned_shms = [
            self._obs_shm,
            self._state_shm,
            self._next_state_shm,
            self._terminal_obs_shm,
            self._terminal_state_shm,
            self._reset_state_shm,
            self._has_terminal_shm,
            self._action_shm,
            self._reward_shm,
            self._done_shm,
            self._metric_value_shm,
            self._metric_present_shm,
        ]

        shared_specs = {
            "observations": (self._obs_shm.name, obs_shape, observation_space.dtype),
            "states": (self._state_shm.name, state_shape, np.float32),
            "next_states": (self._next_state_shm.name, state_shape, np.float32),
            "terminal_observations": (self._terminal_obs_shm.name, obs_shape, observation_space.dtype),
            "terminal_states": (self._terminal_state_shm.name, state_shape, np.float32),
            "reset_states": (self._reset_state_shm.name, state_shape, np.float32),
            "has_terminal": (self._has_terminal_shm.name, (self.num_envs,), np.bool_),
            "actions": (self._action_shm.name, action_shape, action_space.dtype),
            "rewards": (self._reward_shm.name, (self.num_envs,), np.float32),
            "dones": (self._done_shm.name, (self.num_envs,), np.bool_),
            "metric_values": (self._metric_value_shm.name, (self.num_envs, len(SHARED_METRIC_KEYS)), np.float32),
            "metric_present": (self._metric_present_shm.name, (self.num_envs, len(SHARED_METRIC_KEYS)), np.bool_),
        }

        worker_count = min(self.num_workers, math.ceil(len(env_fns) / self.envs_per_worker))
        chunks = []
        for worker_idx in range(worker_count):
            start = worker_idx * self.envs_per_worker
            end = min(start + self.envs_per_worker, len(env_fns))
            if start < end:
                chunks.append(([CloudpickleWrapper(env_fn) for env_fn in env_fns[start:end]], list(range(start, end))))

        ctx = mp.get_context(start_method)
        self._processes = []
        for worker_id, (worker_env_fns, global_indices) in enumerate(chunks):
            parent_conn, child_conn = ctx.Pipe()
            process = ctx.Process(
                target=_worker_loop,
                args=(worker_id, worker_env_fns, global_indices, child_conn, shared_specs, metrics_mode),
                daemon=True,
            )
            process.start()
            child_conn.close()
            self._parent_conns.append(parent_conn)
            self._processes.append(process)
            self._worker_global_indices.append(global_indices)

    def _check_worker_response(self, response):
        status, payload = response
        if status == "error":
            raise RuntimeError(f"ShardedSubprocVecEnv worker failed: {payload}")
        return payload

    def reset(self):
        for conn in self._parent_conns:
            conn.send(("reset", {"return_obs": False}))
        worker_results = [self._check_worker_response(conn.recv()) for conn in self._parent_conns]
        self.reset_infos = [{} for _ in range(self.num_envs)]
        for global_indices, results in zip(self._worker_global_indices, worker_results):
            for global_idx, info in zip(global_indices, results):
                self.reset_infos[global_idx] = info if isinstance(info, dict) else {}
        return self._observations.copy()

    def step_async(self, actions):
        start = time.perf_counter()
        self._actions[...] = np.ascontiguousarray(actions, dtype=self.action_space.dtype)
        self._profile["action_copy_time"] += time.perf_counter() - start
        for conn in self._parent_conns:
            conn.send(("step", None))
        self.waiting = True

    def step_wait(self):
        wait_start = time.perf_counter()
        infos: List[Dict[str, Any]] = [None] * self.num_envs  # type: ignore[list-item]
        for conn, global_indices in zip(self._parent_conns, self._worker_global_indices):
            worker_infos = self._check_worker_response(conn.recv())
            for global_idx, info in zip(global_indices, worker_infos):
                infos[global_idx] = info
        self._profile["worker_wait_time"] += time.perf_counter() - wait_start

        rebuild_start = time.perf_counter()
        if self.metrics_mode == "light":
            metric_infos = self.get_metric_infos()
            for env_idx in range(self.num_envs):
                info = metric_infos[env_idx]
                worker_info = infos[env_idx] or {}
                if "reset_info" in worker_info:
                    info["reset_info"] = worker_info["reset_info"]
                if self._has_terminal[env_idx]:
                    info["terminal_observation"] = self._terminal_observations[env_idx].copy()
                    info["terminal_state"] = self._terminal_states[env_idx].copy()
                    info["reset_state"] = self._reset_states[env_idx].copy()
                infos[env_idx] = info
        elif self.metrics_mode == "train_only":
            infos = [{} for _ in range(self.num_envs)]

        self.waiting = False
        self._profile["info_rebuild_time"] += time.perf_counter() - rebuild_start
        self._profile["steps"] += 1
        return self._observations.copy(), self._rewards.copy(), self._dones.copy(), infos

    def close(self):
        if self.closed:
            return
        if self.waiting:
            for conn in self._parent_conns:
                try:
                    conn.recv()
                except Exception:
                    pass
            self.waiting = False

        for conn in self._parent_conns:
            try:
                conn.send(("close", None))
            except Exception:
                pass
        for conn in self._parent_conns:
            try:
                self._check_worker_response(conn.recv())
            except Exception:
                pass
            try:
                conn.close()
            except Exception:
                pass
        for process in self._processes:
            process.join(timeout=5)
            if process.is_alive():
                process.terminate()
                process.join(timeout=1)

        for shm in self._owned_shms:
            try:
                shm.close()
            except Exception:
                pass
            try:
                shm.unlink()
            except FileNotFoundError:
                pass
        self.closed = True

    def __del__(self):
        try:
            self.close()
        except Exception:
            pass

    def get_states(self):
        return self._states.copy()

    def get_next_states(self):
        return self._next_states.copy()

    def get_terminal_observations(self):
        return self._terminal_observations.copy()

    def get_terminal_states(self):
        return self._terminal_states.copy()

    def get_reset_states(self):
        return self._reset_states.copy()

    def get_has_terminal(self):
        return self._has_terminal.copy()

    def get_metric_infos(self):
        return [
            _light_info_from_metrics(self._metric_values[env_idx], self._metric_present[env_idx])
            for env_idx in range(self.num_envs)
        ]

    def get_profile(self):
        return dict(self._profile)

    def env_method(self, method_name: str, *method_args, indices: Optional[Iterable[int]] = None, **method_kwargs):
        if method_name == "reset":
            for conn in self._parent_conns:
                conn.send(("reset", {"return_obs": True}))
            worker_results = [self._check_worker_response(conn.recv()) for conn in self._parent_conns]
            flat_results = [None] * self.num_envs
            for global_indices, results in zip(self._worker_global_indices, worker_results):
                for global_idx, result in zip(global_indices, results):
                    flat_results[global_idx] = result
            return flat_results if indices is None else [flat_results[i] for i in self._normalize_indices(indices)]

        selected = self._normalize_indices(indices)
        by_worker = self._indices_by_worker(selected)
        results_by_global = {}
        for worker_idx, local_indices in by_worker.items():
            self._parent_conns[worker_idx].send(
                (
                    "env_method",
                    {
                        "method_name": method_name,
                        "args": method_args,
                        "kwargs": method_kwargs,
                        "local_indices": local_indices,
                    },
                )
            )
        for worker_idx, local_indices in by_worker.items():
            result = self._check_worker_response(self._parent_conns[worker_idx].recv())
            for local_idx, value in zip(local_indices, result):
                global_idx = self._worker_global_indices[worker_idx][local_idx]
                results_by_global[global_idx] = value
        return [results_by_global[i] for i in selected]

    def get_attr(self, attr_name: str, indices: Optional[Iterable[int]] = None):
        selected = self._normalize_indices(indices)
        if not self._parent_conns and attr_name in getattr(self, "_initial_attr_cache", {}):
            return [self._initial_attr_cache[attr_name] for _ in selected]
        by_worker = self._indices_by_worker(selected)
        results_by_global = {}
        for worker_idx, local_indices in by_worker.items():
            self._parent_conns[worker_idx].send(
                ("get_attr", {"attr_name": attr_name, "local_indices": local_indices})
            )
        for worker_idx, local_indices in by_worker.items():
            result = self._check_worker_response(self._parent_conns[worker_idx].recv())
            for local_idx, value in zip(local_indices, result):
                global_idx = self._worker_global_indices[worker_idx][local_idx]
                results_by_global[global_idx] = value
        return [results_by_global[i] for i in selected]

    def set_attr(self, attr_name: str, value: Any, indices: Optional[Iterable[int]] = None):
        selected = self._normalize_indices(indices)
        by_worker = self._indices_by_worker(selected)
        for worker_idx, local_indices in by_worker.items():
            self._parent_conns[worker_idx].send(
                ("set_attr", {"attr_name": attr_name, "value": value, "local_indices": local_indices})
            )
        for worker_idx in by_worker:
            self._check_worker_response(self._parent_conns[worker_idx].recv())

    def env_is_wrapped(self, wrapper_class, indices: Optional[Iterable[int]] = None):
        selected = self._normalize_indices(indices)
        return [False for _ in selected]

    def get_images(self):
        return [None] * self.num_envs

    def _normalize_indices(self, indices: Optional[Iterable[int]]):
        if indices is None:
            return list(range(self.num_envs))
        if isinstance(indices, int):
            return [indices]
        return list(indices)

    def _indices_by_worker(self, selected: Sequence[int]):
        selected_set = set(selected)
        by_worker: Dict[int, List[int]] = {}
        for worker_idx, global_indices in enumerate(self._worker_global_indices):
            for local_idx, global_idx in enumerate(global_indices):
                if global_idx in selected_set:
                    by_worker.setdefault(worker_idx, []).append(local_idx)
        return by_worker
