"""Standalone environment collectors for HA-CTSE process-core training.

The collector is intentionally environment-only.  Policy inference, segment
management, rollout storage, and all PPO/process updates stay in the main
process so collected data remains on-policy.
"""

from __future__ import annotations

import multiprocessing as mp
import traceback
from dataclasses import dataclass
from typing import Any

from ha_ctse_process.env_factory import EnvSpec, make_env


@dataclass
class EnvStep:
    obs: Any
    reward: float
    terminated: bool
    truncated: bool
    info: dict


def _worker(remote, parent_remote, config, scenario: str, seed: int, rank: int, scale_mode: str) -> None:
    parent_remote.close()
    env = None
    try:
        env = make_env(
            config,
            EnvSpec(
                scenario=scenario,
                seed=int(seed),
                rank=int(rank),
                scale_mode=scale_mode,
            ),
        )()
        while True:
            command, payload = remote.recv()
            if command == "reset":
                obs, info = env.reset(seed=payload)
                remote.send(("ok", (obs, info)))
            elif command == "step":
                remote.send(("ok", EnvStep(*env.step(payload))))
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
        if env is not None:
            env.close()
        remote.close()


class SyncEnvCollector:
    """Main-process collector used for debugging and tiny smoke runs."""

    def __init__(self, envs):
        self.envs = list(envs)
        self.num_envs = len(self.envs)
        self.spec = {
            "obs_dim": int(self.envs[0].obs_dim),
            "state_dim": int(self.envs[0].state_dim),
            "action_dim": int(self.envs[0].action_dim),
            "n_uavs": int(self.envs[0].n_uavs),
            "action_space": self.envs[0].action_space,
        }

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
    ):
        self.num_envs = int(num_envs)
        self._broken = False
        ctx = mp.get_context(start_method)
        self.remotes, self.work_remotes = zip(*[ctx.Pipe() for _ in range(self.num_envs)])
        self.processes = []
        for rank, (remote, work_remote) in enumerate(zip(self.remotes, self.work_remotes)):
            process = ctx.Process(
                target=_worker,
                args=(work_remote, remote, config, scenario, int(seed), rank, scale_mode),
                daemon=True,
            )
            process.start()
            work_remote.close()
            self.processes.append(process)
        self.spec = self._request_one(0, "spec", None)

    def _recv(self, remote):
        status, payload = remote.recv()
        if status == "error":
            raise RuntimeError(payload)
        return payload

    def _request_one(self, env_id: int, command: str, payload):
        remote = self.remotes[int(env_id)]
        remote.send((command, payload))
        return self._recv(remote)

    def reset_all(self, seed: int):
        for env_id, remote in enumerate(self.remotes):
            remote.send(("reset", int(seed) + env_id))
        results = [self._recv(remote) for remote in self.remotes]
        observations = [obs for obs, _info in results]
        infos = [info for _obs, info in results]
        states = [info.get("state") for info in infos]
        return observations, states, infos

    def reset_one(self, env_id: int, seed: int | None = None):
        return self._request_one(int(env_id), "reset", seed)

    def step(self, actions):
        for remote, action in zip(self.remotes, actions):
            remote.send(("step", action))
        return [self._recv(remote) for remote in self.remotes]

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
                env_id: self._recv(self.remotes[env_id])
                for env_id, _action in pairs
            }
        except Exception:
            self._broken = True
            raise

    def close(self) -> None:
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
            return
        for remote in self.remotes:
            try:
                remote.send(("close", None))
            except (BrokenPipeError, EOFError):
                pass
        for remote in self.remotes:
            try:
                self._recv(remote)
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
