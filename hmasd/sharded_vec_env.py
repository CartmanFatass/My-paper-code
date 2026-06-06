import math
import multiprocessing as mp
from multiprocessing import shared_memory
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence

import numpy as np
from stable_baselines3.common.vec_env import VecEnv
from stable_baselines3.common.vec_env.subproc_vec_env import CloudpickleWrapper


LIGHT_REWARD_KEYS = (
    "coverage_ratio",
    "effective_connected_users",
    "connected_users",
    "system_throughput_mbps",
    "rt_final_health_score",
    "avg_hops",
    "discovery_reward",
    "discovered_users_count",
    "weighted_discovery_reward",
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


def _light_info(info: Dict[str, Any], metrics_mode: str) -> Dict[str, Any]:
    if metrics_mode == "full":
        return dict(info)
    if metrics_mode == "train_only":
        return {}

    result: Dict[str, Any] = {}
    reward_info = info.get("reward_info", {})
    if isinstance(reward_info, dict):
        light_reward_info = {
            key: reward_info[key]
            for key in LIGHT_REWARD_KEYS
            if key in reward_info and np.isscalar(reward_info[key])
        }
        if light_reward_info:
            result["reward_info"] = light_reward_info

    for key in (
        "coverage_ratio",
        "served_users",
        "discovery_reward",
        "discovered_users_count",
        "discovery_progress",
        "total_users",
    ):
        if key in info and np.isscalar(info[key]):
            result[key] = info[key]

    if "reward_components" in info and isinstance(info["reward_components"], dict):
        reward_components = info["reward_components"]
        compact_components = {}
        for key in ("shared_global_reward", "overlap_penalties"):
            value = reward_components.get(key)
            if np.isscalar(value) or isinstance(value, (list, tuple)):
                compact_components[key] = value
        if compact_components:
            result["reward_components"] = compact_components

    return result


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
        action_shm, actions = _attach_shared_array(*shared_specs["actions"])
        reward_shm, rewards = _attach_shared_array(*shared_specs["rewards"])
        done_shm, dones = _attach_shared_array(*shared_specs["dones"])
        shms.extend([obs_shm, state_shm, next_state_shm, action_shm, reward_shm, done_shm])

        def reset_env(local_idx: int, seed=None, reset_step_outputs: bool = True):
            env = envs[local_idx]
            reset_result = env.reset(seed=seed) if seed is not None else env.reset()
            env_obs, info = reset_result
            global_idx = global_indices[local_idx]
            obs[global_idx] = env_obs
            states[global_idx] = info.get("state", np.zeros(states.shape[1], dtype=states.dtype))
            if reset_step_outputs:
                next_states[global_idx] = states[global_idx]
                rewards[global_idx] = 0.0
                dones[global_idx] = False
            return env_obs, info

        while True:
            command, payload = conn.recv()

            if command == "reset":
                results = []
                for local_idx in range(len(envs)):
                    results.append(reset_env(local_idx))
                conn.send(("ok", results))

            elif command == "step":
                infos = []
                for local_idx, env in enumerate(envs):
                    global_idx = global_indices[local_idx]
                    step_obs, reward, terminated, truncated, info = env.step(actions[global_idx].copy())
                    done = bool(terminated or truncated)
                    actual_next_state = info.get(
                        "next_state",
                        np.zeros(next_states.shape[1], dtype=next_states.dtype),
                    )
                    next_states[global_idx] = actual_next_state
                    rewards[global_idx] = float(reward)
                    dones[global_idx] = done

                    compact_info = _light_info(info, metrics_mode)
                    compact_info["next_state"] = next_states[global_idx].copy()
                    if done:
                        compact_info["terminal_observation"] = step_obs
                        compact_info["terminal_state"] = next_states[global_idx].copy()
                        _, reset_info = reset_env(local_idx, reset_step_outputs=False)
                        compact_info["reset_state"] = states[global_idx].copy()
                        compact_info["reset_info"] = _light_info(reset_info, metrics_mode)
                    else:
                        obs[global_idx] = step_obs
                        states[global_idx] = actual_next_state
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

        sample_env = env_fns[0]()
        observation_space = sample_env.observation_space
        action_space = sample_env.action_space
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
        self._action_shm, self._actions = _make_shared_array(action_shape, action_space.dtype)
        self._reward_shm, self._rewards = _make_shared_array((self.num_envs,), np.float32)
        self._done_shm, self._dones = _make_shared_array((self.num_envs,), np.bool_)
        self._owned_shms = [
            self._obs_shm,
            self._state_shm,
            self._next_state_shm,
            self._action_shm,
            self._reward_shm,
            self._done_shm,
        ]

        shared_specs = {
            "observations": (self._obs_shm.name, obs_shape, observation_space.dtype),
            "states": (self._state_shm.name, state_shape, np.float32),
            "next_states": (self._next_state_shm.name, state_shape, np.float32),
            "actions": (self._action_shm.name, action_shape, action_space.dtype),
            "rewards": (self._reward_shm.name, (self.num_envs,), np.float32),
            "dones": (self._done_shm.name, (self.num_envs,), np.bool_),
        }

        worker_count = min(self.num_workers, math.ceil(len(env_fns) / self.envs_per_worker))
        chunks = []
        for worker_idx in range(worker_count):
            start = worker_idx * self.envs_per_worker
            end = min(start + self.envs_per_worker, len(env_fns))
            if start < end:
                chunks.append(([CloudpickleWrapper(env_fn) for env_fn in env_fns[start:end]], list(range(start, end))))

        ctx = mp.get_context(start_method)
        self._parent_conns = []
        self._processes = []
        self._worker_global_indices = []
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
            conn.send(("reset", None))
        worker_results = [self._check_worker_response(conn.recv()) for conn in self._parent_conns]
        self.reset_infos = [{} for _ in range(self.num_envs)]
        for global_indices, results in zip(self._worker_global_indices, worker_results):
            for global_idx, result in zip(global_indices, results):
                if isinstance(result, tuple) and len(result) == 2:
                    self.reset_infos[global_idx] = result[1]
        return self._observations.copy()

    def step_async(self, actions):
        self._actions[...] = np.asarray(actions, dtype=self.action_space.dtype)
        for conn in self._parent_conns:
            conn.send(("step", None))
        self.waiting = True

    def step_wait(self):
        infos: List[Dict[str, Any]] = [None] * self.num_envs  # type: ignore[list-item]
        for conn, global_indices in zip(self._parent_conns, self._worker_global_indices):
            worker_infos = self._check_worker_response(conn.recv())
            for global_idx, info in zip(global_indices, worker_infos):
                infos[global_idx] = info
        self.waiting = False
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

    def env_method(self, method_name: str, *method_args, indices: Optional[Iterable[int]] = None, **method_kwargs):
        if method_name == "reset":
            for conn in self._parent_conns:
                conn.send(("reset", None))
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
