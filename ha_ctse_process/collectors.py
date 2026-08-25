"""Standalone environment collectors for HA-CTSE process-core training.

The collector is intentionally environment-only.  Policy inference, segment
management, rollout storage, and all PPO/process updates stay in the main
process so collected data remains on-policy.
"""

from __future__ import annotations

import multiprocessing as mp
from multiprocessing import shared_memory
import hashlib
import io
import pickle
import struct
import traceback
from dataclasses import dataclass
from typing import Any

from gymnasium.utils import EzPickle

from ha_ctse_process.env_factory import EnvSpec, make_env


EVENT_SNAPSHOT_CAPABILITY_NAME = "variable_roster_event_snapshot"
EVENT_SNAPSHOT_CAPABILITY_VERSION = 1
TRAINING_SNAPSHOT_CAPABILITY_NAME = "standalone_collector_training_state"
TRAINING_SNAPSHOT_CAPABILITY_VERSION = 1

PIPE_PICKLE_TRANSPORT = "pipe_pickle"
SHARED_MEMORY_TRANSPORT = "shared_memory_v1"
SUPPORTED_SUBPROC_TRANSPORTS = frozenset(
    {PIPE_PICKLE_TRANSPORT, SHARED_MEMORY_TRANSPORT}
)
# The 31-sample fixed-machine collector benchmark proves full semantic/RNG
# equivalence and a strictly positive end-to-end median improvement for v1.
DEFAULT_SUBPROC_TRANSPORT = SHARED_MEMORY_TRANSPORT
DEFAULT_SHARED_MEMORY_BYTES = 16 * 1024 * 1024

_SHARED_RESULT_MAGIC = b"HACOLV1\0"
_SHARED_RESULT_HEADER = struct.Struct("<8sIQQ")
_SHARED_RESULT_VERSION = 1


def _event_capability(env) -> dict[str, Any]:
    capability = getattr(env, "event_runtime_snapshot_capability", None)
    snapshot = getattr(env, "snapshot_event_runtime", None)
    restore = getattr(env, "restore_event_runtime", None)
    if not callable(capability) or not callable(snapshot) or not callable(restore):
        raise RuntimeError("environment does not expose event-runtime snapshot capability")
    value = dict(capability())
    if value.get("name") != EVENT_SNAPSHOT_CAPABILITY_NAME or int(
        value.get("version", -1)
    ) != EVENT_SNAPSHOT_CAPABILITY_VERSION:
        raise RuntimeError("environment event-runtime snapshot capability is unsupported")
    return value


def _callable_identity(value) -> tuple[str, str, int]:
    target = getattr(value, "__func__", value)
    return (
        str(getattr(target, "__module__", "")),
        str(getattr(target, "__qualname__", type(target).__qualname__)),
        id(target),
    )


def _event_environment_identity(env) -> tuple[Any, ...]:
    return (
        id(env),
        type(env).__module__,
        type(env).__qualname__,
        _callable_identity(getattr(env, "event_runtime_snapshot_capability", None)),
        _callable_identity(getattr(env, "snapshot_event_runtime", None)),
        _callable_identity(getattr(env, "restore_event_runtime", None)),
    )


def _env_spec(env) -> dict[str, Any]:
    """Return the strict, pickle-stable collector-facing environment ABI."""

    action_space = env.action_space
    dtype = getattr(action_space, "dtype", None)
    shape = getattr(action_space, "shape", None)
    return {
        "environment_type": f"{type(env).__module__}.{type(env).__qualname__}",
        "obs_dim": int(env.obs_dim),
        "state_dim": int(env.state_dim),
        "action_dim": int(env.action_dim),
        "n_uavs": int(env.n_uavs),
        "action_space_type": (
            f"{type(action_space).__module__}.{type(action_space).__qualname__}"
        ),
        "action_space_dtype": None if dtype is None else str(dtype),
        "action_space_shape": None if shape is None else tuple(int(v) for v in shape),
        "action_space_n": (
            None if not hasattr(action_space, "n") else int(action_space.n)
        ),
    }


def _rebuild_exact_ezpickle(cls, state: dict[str, Any]):
    instance = cls.__new__(cls)
    instance.__dict__.update(state)
    return instance


class _TrainingStatePickler(pickle.Pickler):
    """Bypass constructor-only EzPickle reductions for live environment state."""

    def reducer_override(self, obj):
        if isinstance(obj, EzPickle):
            state = dict(obj.__dict__)
            # Pygame render handles are process-local presentation resources,
            # not training state, and cannot be serialized.  A resumed headless
            # trainer recreates them lazily if rendering is requested later.
            for key in ("screen", "viewer", "game_font"):
                if key in state:
                    state[key] = None
            return (_rebuild_exact_ezpickle, (type(obj), state))
        return NotImplemented


def _training_state_dumps(value: Any) -> bytes:
    output = io.BytesIO()
    _TrainingStatePickler(output, protocol=pickle.HIGHEST_PROTOCOL).dump(value)
    return output.getvalue()


def _environment_spec_digest(spec: dict[str, Any]) -> str:
    return hashlib.sha256(
        pickle.dumps(spec, protocol=pickle.HIGHEST_PROTOCOL)
    ).hexdigest()


def _snapshot_training_env(env) -> dict[str, Any]:
    try:
        payload = _training_state_dumps(env)
    except Exception as exc:
        raise RuntimeError(
            "environment does not support exact protocol-5 training-state snapshot"
        ) from exc
    environment_spec = _env_spec(env)
    return {
        "pickle_protocol": int(pickle.HIGHEST_PROTOCOL),
        "environment_spec": environment_spec,
        "environment_spec_sha256": _environment_spec_digest(environment_spec),
        "payload_sha256": hashlib.sha256(payload).hexdigest(),
        "payload": payload,
    }


def _restore_training_env(snapshot: Any):
    if not isinstance(snapshot, dict) or set(snapshot) != {
        "pickle_protocol",
        "environment_spec",
        "environment_spec_sha256",
        "payload_sha256",
        "payload",
    }:
        raise ValueError("worker training-state snapshot field mismatch")
    if int(snapshot["pickle_protocol"]) != int(pickle.HIGHEST_PROTOCOL):
        raise ValueError("worker training-state pickle protocol mismatch")
    expected_spec = dict(snapshot["environment_spec"])
    if _environment_spec_digest(expected_spec) != str(
        snapshot["environment_spec_sha256"]
    ):
        raise ValueError("worker training-state environment spec digest mismatch")
    payload = snapshot["payload"]
    if not isinstance(payload, bytes):
        raise ValueError("worker training-state payload must be bytes")
    if hashlib.sha256(payload).hexdigest() != str(snapshot["payload_sha256"]):
        raise ValueError("worker training-state payload digest mismatch")
    try:
        restored = pickle.loads(payload)
    except Exception as exc:
        raise ValueError("worker training-state payload cannot be restored") from exc
    if _env_spec(restored) != expected_spec:
        close = getattr(restored, "close", None)
        if callable(close):
            close()
        raise ValueError("worker training-state environment spec mismatch")
    return restored


def _collector_training_snapshot(worker_snapshots: list[dict[str, Any]]) -> dict[str, Any]:
    if not worker_snapshots:
        raise RuntimeError("training-state snapshot requires at least one worker")
    return {
        "snapshot_capability_name": TRAINING_SNAPSHOT_CAPABILITY_NAME,
        "snapshot_capability_version": TRAINING_SNAPSHOT_CAPABILITY_VERSION,
        "worker_count": len(worker_snapshots),
        "workers": worker_snapshots,
    }


def _validate_training_snapshot(snapshot: Any, num_envs: int) -> dict[str, Any]:
    if not isinstance(snapshot, dict) or set(snapshot) != {
        "snapshot_capability_name",
        "snapshot_capability_version",
        "worker_count",
        "workers",
    }:
        raise ValueError("collector training-state snapshot field mismatch")
    if snapshot["snapshot_capability_name"] != TRAINING_SNAPSHOT_CAPABILITY_NAME:
        raise ValueError("collector training-state capability name mismatch")
    if int(snapshot["snapshot_capability_version"]) != (
        TRAINING_SNAPSHOT_CAPABILITY_VERSION
    ):
        raise ValueError("collector training-state capability version mismatch")
    if int(snapshot["worker_count"]) != int(num_envs):
        raise ValueError("collector training-state worker count mismatch")
    workers = snapshot["workers"]
    if not isinstance(workers, list) or len(workers) != int(num_envs):
        raise ValueError("collector training-state worker payload count mismatch")
    return snapshot


def _write_shared_result(
    memory: shared_memory.SharedMemory,
    capacity: int,
    generation: int,
    value: Any,
) -> None:
    payload = pickle.dumps(value, protocol=pickle.HIGHEST_PROTOCOL)
    required = _SHARED_RESULT_HEADER.size + len(payload)
    if required > int(capacity):
        raise RuntimeError(
            "collector shared-memory payload exceeds configured capacity: "
            f"required={required} capacity={capacity}"
        )
    start = _SHARED_RESULT_HEADER.size
    memory.buf[start : start + len(payload)] = payload
    memory.buf[: _SHARED_RESULT_HEADER.size] = _SHARED_RESULT_HEADER.pack(
        _SHARED_RESULT_MAGIC,
        _SHARED_RESULT_VERSION,
        int(generation),
        len(payload),
    )


def _read_shared_result(
    memory: shared_memory.SharedMemory,
    capacity: int,
    expected_generation: int,
) -> Any:
    magic, version, generation, payload_length = _SHARED_RESULT_HEADER.unpack(
        bytes(memory.buf[: _SHARED_RESULT_HEADER.size])
    )
    if magic != _SHARED_RESULT_MAGIC or int(version) != _SHARED_RESULT_VERSION:
        raise RuntimeError("collector shared-memory transport header mismatch")
    if int(generation) != int(expected_generation):
        raise RuntimeError("collector shared-memory transport generation mismatch")
    if payload_length <= 0 or _SHARED_RESULT_HEADER.size + payload_length > int(capacity):
        raise RuntimeError("collector shared-memory transport length mismatch")
    start = _SHARED_RESULT_HEADER.size
    payload = bytes(memory.buf[start : start + payload_length])
    try:
        return pickle.loads(payload)
    except Exception as exc:
        raise RuntimeError("collector shared-memory payload cannot be decoded") from exc


def _collector_snapshot(worker_snapshots: list[dict[str, Any]]) -> dict[str, Any]:
    if not worker_snapshots:
        raise RuntimeError("event-runtime snapshot requires at least one worker")
    return {
        "snapshot_capability_name": EVENT_SNAPSHOT_CAPABILITY_NAME,
        "snapshot_capability_version": EVENT_SNAPSHOT_CAPABILITY_VERSION,
        "collector_active_presentation": [
            snapshot.get("active_presentation") for snapshot in worker_snapshots
        ],
        "pending_membership_transaction": [
            snapshot.get("pending_membership_transaction")
            for snapshot in worker_snapshots
        ],
        "collector_pending_command_response_state": [
            snapshot.get("pending_command_response_state")
            for snapshot in worker_snapshots
        ],
        "worker_environment_snapshot": [
            snapshot.get("worker_environment_snapshot")
            for snapshot in worker_snapshots
        ],
        "environment_rng_state": [
            snapshot.get("environment_rng_state") for snapshot in worker_snapshots
        ],
        "workers": worker_snapshots,
    }


def _validate_collector_snapshot(snapshot: Any, num_envs: int) -> dict[str, Any]:
    if not isinstance(snapshot, dict):
        raise ValueError("collector event snapshot must be a dictionary")
    if snapshot.get("snapshot_capability_name") != EVENT_SNAPSHOT_CAPABILITY_NAME:
        raise ValueError("collector event snapshot capability name mismatch")
    if int(snapshot.get("snapshot_capability_version", -1)) != (
        EVENT_SNAPSHOT_CAPABILITY_VERSION
    ):
        raise ValueError("collector event snapshot capability version mismatch")
    workers = snapshot.get("workers")
    if not isinstance(workers, list) or len(workers) != int(num_envs):
        raise ValueError("collector event snapshot worker count mismatch")
    return snapshot


@dataclass
class EnvStep:
    obs: Any
    reward: float
    terminated: bool
    truncated: bool
    info: dict


@dataclass
class EventEnvStep:
    reward: float
    terminated: bool
    truncated: bool
    info: dict
    next_transaction: Any | None


def _worker(
    remote,
    parent_remote,
    config,
    scenario: str,
    seed: int,
    rank: int,
    scale_mode: str,
    transport: str,
    shared_memory_name: str | None,
    shared_memory_bytes: int,
    env_factory,
) -> None:
    parent_remote.close()
    env = None
    result_memory = None
    shared_generation = 0
    pinned_event_capability = None
    pinned_event_identity = None
    prepared_training_env = None
    prepared_event_capability = None

    def ensure_event_capability() -> dict[str, Any]:
        nonlocal pinned_event_capability, pinned_event_identity
        identity = _event_environment_identity(env)
        if pinned_event_capability is None:
            pinned_event_capability = _event_capability(env)
            pinned_event_identity = identity
        elif identity != pinned_event_identity:
            raise RuntimeError("worker event environment identity changed after pinning")
        return dict(pinned_event_capability)

    def send_result(value: Any) -> None:
        nonlocal shared_generation
        if transport == PIPE_PICKLE_TRANSPORT:
            remote.send(("ok", value))
            return
        if result_memory is None:
            raise RuntimeError("collector shared-memory transport is not initialized")
        shared_generation += 1
        _write_shared_result(
            result_memory,
            shared_memory_bytes,
            shared_generation,
            value,
        )
        remote.send(("ok_shm", shared_generation))

    try:
        if transport not in SUPPORTED_SUBPROC_TRANSPORTS:
            raise ValueError(f"unsupported collector transport: {transport!r}")
        if transport == SHARED_MEMORY_TRANSPORT:
            if not shared_memory_name:
                raise RuntimeError("collector shared-memory name is missing")
            result_memory = shared_memory.SharedMemory(name=shared_memory_name)
        env = (
            env_factory()
            if env_factory is not None
            else make_env(
                config,
                EnvSpec(
                    scenario=scenario,
                    seed=int(seed),
                    rank=int(rank),
                    scale_mode=scale_mode,
                ),
            )()
        )
        while True:
            command, payload = remote.recv()
            if command == "reset":
                obs, info = env.reset(seed=payload)
                send_result((obs, info))
            elif command == "step":
                send_result(EnvStep(*env.step(payload)))
            elif command == "spec":
                remote.send(
                    (
                        "ok",
                        {
                            "obs_dim": int(env.obs_dim),
                            "state_dim": int(env.state_dim),
                            "action_dim": int(env.action_dim),
                            "n_uavs": int(env.n_uavs),
                            "action_space": env.action_space,
                        },
                    )
                )
            elif command == "training_spec":
                remote.send(("ok", _env_spec(env)))
            elif command == "event_capability":
                remote.send(("ok", ensure_event_capability()))
            elif command == "event_reset":
                ensure_event_capability()
                remote.send(("ok", env.reset_event_runtime(int(payload))))
            elif command == "event_step":
                ensure_event_capability()
                result = env.step_event_runtime(payload)
                send_result(EventEnvStep(**result.__dict__))
            elif command == "event_snapshot":
                ensure_event_capability()
                remote.send(("ok", env.snapshot_event_runtime()))
            elif command == "event_restore":
                ensure_event_capability()
                env.restore_event_runtime(payload)
                remote.send(("ok", None))
            elif command == "training_snapshot":
                remote.send(("ok", _snapshot_training_env(env)))
            elif command == "training_restore_prepare":
                if prepared_training_env is not None:
                    raise RuntimeError("worker already has a prepared training restore")
                restored = _restore_training_env(payload)
                restored_capability = None
                if pinned_event_capability is not None:
                    restored_capability = _event_capability(restored)
                    if restored_capability != pinned_event_capability:
                        close = getattr(restored, "close", None)
                        if callable(close):
                            close()
                        raise RuntimeError(
                            "restored event environment capability differs from pinned capability"
                        )
                prepared_training_env = restored
                prepared_event_capability = restored_capability
                remote.send(("ok", _env_spec(restored)))
            elif command == "training_restore_commit":
                if prepared_training_env is None:
                    raise RuntimeError("worker has no prepared training restore")
                old_env = env
                env = prepared_training_env
                pinned_event_capability = prepared_event_capability
                pinned_event_identity = (
                    None
                    if pinned_event_capability is None
                    else _event_environment_identity(env)
                )
                prepared_training_env = None
                prepared_event_capability = None
                close = getattr(old_env, "close", None)
                if callable(close):
                    try:
                        close()
                    except Exception:
                        pass
                remote.send(("ok", _env_spec(env)))
            elif command == "training_restore_abort":
                if prepared_training_env is not None:
                    close = getattr(prepared_training_env, "close", None)
                    if callable(close):
                        close()
                    prepared_training_env = None
                    prepared_event_capability = None
                remote.send(("ok", None))
            elif command == "close":
                remote.send(("ok", None))
                break
            else:
                raise RuntimeError(f"Unknown collector command: {command}")
    except KeyboardInterrupt:
        pass
    except Exception:
        remote.send(("error", traceback.format_exc()))
    finally:
        if prepared_training_env is not None:
            close = getattr(prepared_training_env, "close", None)
            if callable(close):
                close()
        if env is not None:
            env.close()
        if result_memory is not None:
            result_memory.close()
        remote.close()


class SyncEnvCollector:
    """Main-process collector used for debugging and tiny smoke runs."""

    def __init__(self, envs):
        self.envs = list(envs)
        self.num_envs = len(self.envs)
        if self.num_envs <= 0:
            raise ValueError("collector requires at least one environment")
        self._event_capability_value: dict[str, Any] | None = None
        self._event_environment_identities: tuple[tuple[Any, ...], ...] | None = None
        self._training_environment_specs = tuple(_env_spec(env) for env in self.envs)
        self.spec = {
            "obs_dim": int(self.envs[0].obs_dim),
            "state_dim": int(self.envs[0].state_dim),
            "action_dim": int(self.envs[0].action_dim),
            "n_uavs": int(self.envs[0].n_uavs),
            "action_space": self.envs[0].action_space,
        }

    def _current_event_identities(self) -> tuple[tuple[Any, ...], ...]:
        return tuple(_event_environment_identity(env) for env in self.envs)

    def _ensure_event_capability(self) -> dict[str, Any]:
        identities = self._current_event_identities()
        if self._event_capability_value is None:
            values = [_event_capability(env) for env in self.envs]
            if any(value != values[0] for value in values[1:]):
                raise RuntimeError("event-runtime collector workers disagree on capability")
            self._event_capability_value = dict(values[0])
            self._event_environment_identities = identities
        elif identities != self._event_environment_identities:
            raise RuntimeError("event-runtime collector environment identity changed after pinning")
        return dict(self._event_capability_value)

    def reset_all(self, seed: int):
        observations = []
        states = []
        infos = []
        for env_id, env in enumerate(self.envs):
            obs, info = env.reset(seed=int(seed) + env_id)
            observations.append(obs)
            states.append(info.get("state"))
            infos.append(info)
        return observations, states, infos

    def reset_one(self, env_id: int, seed: int | None = None):
        obs, info = self.envs[int(env_id)].reset(seed=seed)
        return obs, info

    def step(self, actions):
        return [EnvStep(*env.step(action)) for env, action in zip(self.envs, actions)]

    def event_runtime_capability(self) -> dict[str, Any]:
        return self._ensure_event_capability()

    def reset_event_runtime(self, episode_ids) -> list[Any]:
        self._ensure_event_capability()
        ids = tuple(int(value) for value in episode_ids)
        if len(ids) != self.num_envs:
            raise ValueError("event reset episode-id count mismatch")
        return [
            env.reset_event_runtime(episode_id)
            for env, episode_id in zip(self.envs, ids)
        ]

    def step_event_runtime(self, routed_actions) -> list[EventEnvStep]:
        self._ensure_event_capability()
        rows = tuple(routed_actions)
        if len(rows) != self.num_envs:
            raise ValueError("event action batch count mismatch")
        return [
            EventEnvStep(**env.step_event_runtime(actions).__dict__)
            for env, actions in zip(self.envs, rows)
        ]

    def snapshot_event_runtime(self) -> dict[str, Any]:
        self._ensure_event_capability()
        worker_snapshots = [dict(env.snapshot_event_runtime()) for env in self.envs]
        return _collector_snapshot(worker_snapshots)

    def restore_event_runtime(self, snapshot: dict[str, Any]) -> None:
        value = _validate_collector_snapshot(snapshot, self.num_envs)
        self._ensure_event_capability()
        for env, worker_snapshot in zip(self.envs, value["workers"]):
            env.restore_event_runtime(worker_snapshot)

    def snapshot_training_state(self) -> dict[str, Any]:
        return _collector_training_snapshot(
            [_snapshot_training_env(env) for env in self.envs]
        )

    def restore_training_state(self, snapshot: dict[str, Any]) -> None:
        value = _validate_training_snapshot(snapshot, self.num_envs)
        restored_envs = []
        try:
            for expected_spec, worker_snapshot in zip(
                self._training_environment_specs, value["workers"]
            ):
                if dict(worker_snapshot.get("environment_spec", {})) != expected_spec:
                    raise ValueError("collector training-state environment spec mismatch")
                restored_envs.append(_restore_training_env(worker_snapshot))
            restored_capability = None
            if self._event_capability_value is not None:
                capabilities = [_event_capability(env) for env in restored_envs]
                if any(
                    capability != self._event_capability_value
                    for capability in capabilities
                ):
                    raise ValueError(
                        "restored event environment capability differs from pinned capability"
                    )
                restored_capability = dict(self._event_capability_value)
        except Exception:
            for env in restored_envs:
                close = getattr(env, "close", None)
                if callable(close):
                    close()
            raise

        old_envs = self.envs
        self.envs = restored_envs
        self._event_capability_value = restored_capability
        self._event_environment_identities = (
            None if restored_capability is None else self._current_event_identities()
        )
        for env in old_envs:
            close = getattr(env, "close", None)
            if callable(close):
                try:
                    close()
                except Exception:
                    pass

    def close(self) -> None:
        for env in self.envs:
            env.close()


class SubprocEnvCollector:
    """Subprocess collector with a main-process policy/update barrier."""

    def __init__(
        self,
        config,
        scenario: str,
        seed: int,
        num_envs: int,
        scale_mode: str,
        start_method: str = "spawn",
        transport: str = DEFAULT_SUBPROC_TRANSPORT,
        shared_memory_bytes: int = DEFAULT_SHARED_MEMORY_BYTES,
        env_factories=None,
    ):
        self.num_envs = int(num_envs)
        if self.num_envs <= 0:
            raise ValueError("collector requires at least one environment")
        self.transport = str(transport)
        if self.transport not in SUPPORTED_SUBPROC_TRANSPORTS:
            raise ValueError(f"unsupported collector transport: {self.transport!r}")
        self.shared_memory_bytes = int(shared_memory_bytes)
        if self.transport == SHARED_MEMORY_TRANSPORT and (
            self.shared_memory_bytes <= _SHARED_RESULT_HEADER.size
        ):
            raise ValueError("collector shared-memory capacity is too small")
        if env_factories is None:
            factories = [None] * self.num_envs
        else:
            factories = list(env_factories)
            if len(factories) != self.num_envs or any(
                not callable(factory) for factory in factories
            ):
                raise ValueError("env_factories must contain one callable per worker")
        self._broken = False
        self._closed = False
        self._event_capability_value: dict[str, Any] | None = None
        self._event_process_identities: tuple[tuple[int, int | None], ...] | None = None
        ctx = mp.get_context(start_method)
        self.remotes, self.work_remotes = zip(*[ctx.Pipe() for _ in range(self.num_envs)])
        self._result_memories: list[shared_memory.SharedMemory | None] = []
        for _ in range(self.num_envs):
            self._result_memories.append(
                shared_memory.SharedMemory(create=True, size=self.shared_memory_bytes)
                if self.transport == SHARED_MEMORY_TRANSPORT
                else None
            )
        self._shared_generations = [0] * self.num_envs
        self.processes = []
        try:
            for rank, (remote, work_remote, factory) in enumerate(
                zip(self.remotes, self.work_remotes, factories)
            ):
                memory = self._result_memories[rank]
                process = ctx.Process(
                    target=_worker,
                    args=(
                        work_remote,
                        remote,
                        config,
                        scenario,
                        int(seed),
                        rank,
                        scale_mode,
                        self.transport,
                        None if memory is None else memory.name,
                        self.shared_memory_bytes,
                        factory,
                    ),
                    daemon=True,
                )
                process.start()
                work_remote.close()
                self.processes.append(process)
            specs = [
                self._request_one(env_id, "spec", None)
                for env_id in range(self.num_envs)
            ]
            self.spec = specs[0]
            self._training_environment_specs = tuple(
                dict(self._request_one(env_id, "training_spec", None))
                for env_id in range(self.num_envs)
            )
        except Exception:
            self._broken = True
            self.close()
            raise

    def _process_identities(self) -> tuple[tuple[int, int | None], ...]:
        return tuple((id(process), process.pid) for process in self.processes)

    def _ensure_event_processes(self) -> None:
        identities = self._process_identities()
        if self._event_process_identities is not None and (
            identities != self._event_process_identities
        ):
            raise RuntimeError("event-runtime collector worker identity changed after pinning")
        if any(not process.is_alive() for process in self.processes):
            raise RuntimeError("event-runtime collector worker is not alive")

    def _recv(self, remote, env_id: int):
        status, payload = remote.recv()
        if status == "error":
            self._broken = True
            raise RuntimeError(payload)
        if status == "ok_shm":
            if self.transport != SHARED_MEMORY_TRANSPORT:
                self._broken = True
                raise RuntimeError("worker used unexpected shared-memory transport")
            expected_generation = self._shared_generations[int(env_id)] + 1
            if int(payload) != expected_generation:
                self._broken = True
                raise RuntimeError("collector shared-memory notification generation mismatch")
            memory = self._result_memories[int(env_id)]
            if memory is None:
                self._broken = True
                raise RuntimeError("collector shared-memory buffer is missing")
            value = _read_shared_result(
                memory,
                self.shared_memory_bytes,
                expected_generation,
            )
            self._shared_generations[int(env_id)] = expected_generation
            return value
        if status != "ok":
            self._broken = True
            raise RuntimeError(f"unknown collector response status: {status!r}")
        return payload

    def _request_one(self, env_id: int, command: str, payload):
        remote = self.remotes[int(env_id)]
        remote.send((command, payload))
        return self._recv(remote, int(env_id))

    def reset_all(self, seed: int):
        for env_id, remote in enumerate(self.remotes):
            remote.send(("reset", int(seed) + env_id))
        results = [
            self._recv(remote, env_id) for env_id, remote in enumerate(self.remotes)
        ]
        observations = [obs for obs, _info in results]
        infos = [info for _obs, info in results]
        states = [info.get("state") for info in infos]
        return observations, states, infos

    def reset_one(self, env_id: int, seed: int | None = None):
        return self._request_one(int(env_id), "reset", seed)

    def step(self, actions):
        rows = tuple(actions)
        if len(rows) != self.num_envs:
            raise ValueError("collector action batch count mismatch")
        for remote, action in zip(self.remotes, rows):
            remote.send(("step", action))
        return [
            self._recv(remote, env_id) for env_id, remote in enumerate(self.remotes)
        ]

    def step_selected(self, indexed_actions):
        if bool(getattr(self, "_broken", False)):
            raise RuntimeError("subprocess collector is broken and cannot be reused")
        pairs = [(int(env_id), action) for env_id, action in indexed_actions]
        env_ids = [env_id for env_id, _action in pairs]
        if len(env_ids) != len(set(env_ids)):
            raise ValueError("step_selected received duplicate env_id")
        if any(env_id < 0 or env_id >= self.num_envs for env_id in env_ids):
            raise ValueError("step_selected env_id out of range")
        try:
            for env_id, action in pairs:
                self.remotes[env_id].send(("step", action))
            return {
                env_id: self._recv(self.remotes[env_id], env_id)
                for env_id, _action in pairs
            }
        except Exception:
            self._broken = True
            raise

    def event_runtime_capability(self) -> dict[str, Any]:
        self._ensure_event_processes()
        if self._event_capability_value is not None:
            return dict(self._event_capability_value)
        for remote in self.remotes:
            remote.send(("event_capability", None))
        values = [
            dict(self._recv(remote, env_id))
            for env_id, remote in enumerate(self.remotes)
        ]
        if any(value != values[0] for value in values[1:]):
            raise RuntimeError("event-runtime collector workers disagree on capability")
        self._event_capability_value = dict(values[0])
        self._event_process_identities = self._process_identities()
        return dict(self._event_capability_value)

    def reset_event_runtime(self, episode_ids) -> list[Any]:
        self.event_runtime_capability()
        ids = tuple(int(value) for value in episode_ids)
        if len(ids) != self.num_envs:
            raise ValueError("event reset episode-id count mismatch")
        for remote, episode_id in zip(self.remotes, ids):
            remote.send(("event_reset", episode_id))
        return [
            self._recv(remote, env_id) for env_id, remote in enumerate(self.remotes)
        ]

    def step_event_runtime(self, routed_actions) -> list[EventEnvStep]:
        self.event_runtime_capability()
        rows = tuple(routed_actions)
        if len(rows) != self.num_envs:
            raise ValueError("event action batch count mismatch")
        for remote, actions in zip(self.remotes, rows):
            remote.send(("event_step", actions))
        return [
            self._recv(remote, env_id) for env_id, remote in enumerate(self.remotes)
        ]

    def snapshot_event_runtime(self) -> dict[str, Any]:
        self.event_runtime_capability()
        for remote in self.remotes:
            remote.send(("event_snapshot", None))
        worker_snapshots = [
            dict(self._recv(remote, env_id))
            for env_id, remote in enumerate(self.remotes)
        ]
        return _collector_snapshot(worker_snapshots)

    def restore_event_runtime(self, snapshot: dict[str, Any]) -> None:
        value = _validate_collector_snapshot(snapshot, self.num_envs)
        self.event_runtime_capability()
        for remote, worker_snapshot in zip(self.remotes, value["workers"]):
            remote.send(("event_restore", worker_snapshot))
        for env_id, remote in enumerate(self.remotes):
            self._recv(remote, env_id)

    def snapshot_training_state(self) -> dict[str, Any]:
        for remote in self.remotes:
            remote.send(("training_snapshot", None))
        worker_snapshots = [
            dict(self._recv(remote, env_id))
            for env_id, remote in enumerate(self.remotes)
        ]
        return _collector_training_snapshot(worker_snapshots)

    def restore_training_state(self, snapshot: dict[str, Any]) -> None:
        value = _validate_training_snapshot(snapshot, self.num_envs)
        for expected_spec, worker_snapshot in zip(
            self._training_environment_specs, value["workers"]
        ):
            if dict(worker_snapshot.get("environment_spec", {})) != expected_spec:
                raise ValueError("collector training-state environment spec mismatch")

        prepared_env_ids: list[int] = []
        try:
            for env_id, (remote, worker_snapshot) in enumerate(
                zip(self.remotes, value["workers"])
            ):
                remote.send(("training_restore_prepare", worker_snapshot))
                actual_spec = dict(self._recv(remote, env_id))
                if actual_spec != self._training_environment_specs[env_id]:
                    raise ValueError("prepared training-state environment spec mismatch")
                prepared_env_ids.append(env_id)
        except Exception:
            for env_id in prepared_env_ids:
                try:
                    self.remotes[env_id].send(("training_restore_abort", None))
                    self._recv(self.remotes[env_id], env_id)
                except Exception:
                    self._broken = True
            raise

        for remote in self.remotes:
            remote.send(("training_restore_commit", None))
        for env_id, remote in enumerate(self.remotes):
            actual_spec = dict(self._recv(remote, env_id))
            if actual_spec != self._training_environment_specs[env_id]:
                self._broken = True
                raise RuntimeError("committed training-state environment spec mismatch")
        if self._event_capability_value is not None:
            # Worker-side prepare already checked equality with the pinned value.
            self._ensure_event_processes()

    def _release_shared_memory(self) -> None:
        for memory in getattr(self, "_result_memories", ()):
            if memory is None:
                continue
            try:
                memory.close()
            except OSError:
                pass
            try:
                memory.unlink()
            except FileNotFoundError:
                pass

    def close(self) -> None:
        if bool(getattr(self, "_closed", False)):
            return
        self._closed = True
        if bool(getattr(self, "_broken", False)):
            for remote in self.remotes:
                try:
                    remote.close()
                except (BrokenPipeError, EOFError, OSError):
                    pass
            for process in self.processes:
                if process.is_alive():
                    process.terminate()
                process.join(timeout=1.0)
            self._release_shared_memory()
            return
        for remote in self.remotes:
            try:
                remote.send(("close", None))
            except (BrokenPipeError, EOFError):
                pass
        for remote in self.remotes:
            try:
                env_id = self.remotes.index(remote)
                self._recv(remote, env_id)
            except (BrokenPipeError, EOFError, OSError, RuntimeError):
                pass
            try:
                remote.close()
            except OSError:
                pass
        for process in self.processes:
            process.join(timeout=2.0)
            if process.is_alive():
                process.terminate()
                process.join(timeout=1.0)
        self._release_shared_memory()
