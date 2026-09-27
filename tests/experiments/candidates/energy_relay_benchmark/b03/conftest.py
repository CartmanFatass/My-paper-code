"""Shared tiny fixtures for energy_relay_benchmark B03 tests (CPU)."""

from __future__ import annotations

from dataclasses import replace

import numpy as np
import pytest

from experiments.candidates.energy_relay_benchmark.b02.configuration import B02Spec
from experiments.candidates.energy_relay_benchmark.b03.configuration import make_b03_config
from experiments.candidates.uav_service_auxiliary.b01.native import make_env


def _tiny_spec(**changes) -> B02Spec:
    """2 lanes x 20 steps (episode 20), hidden 32, one PPO epoch, a checkpoint per rollout."""
    spec = replace(B02Spec(), seed=317771, rollouts=2, rollout_length=20, episode_length=20,
                   hidden_size=32, gru_hidden_size=32, ppo_epochs=1,
                   checkpoint_every_transitions=40)
    return replace(spec, **changes)


@pytest.fixture(scope="session")
def tiny_spec():
    """The tiny-spec factory (conftest helpers are not importable without packages)."""
    return _tiny_spec


@pytest.fixture(scope="session")
def tiny_config():
    return make_b03_config(_tiny_spec())


@pytest.fixture(scope="session")
def live_frames(tiny_config):
    """(raw env snapshot, state, observations) from two worlds under random bounded actions."""
    rng = np.random.default_rng(20260927)
    frames = []
    for seed in (952011, 953011):
        env = make_env(tiny_config, seed)
        try:
            obs, info = env.reset(seed=seed)
            for step in range(13):
                raw = env.env
                frames.append({
                    "state": np.asarray(info["state"] if step == 0 else info["next_state"],
                                        dtype=np.float32),
                    "obs": np.asarray(obs, dtype=np.float32),
                    "uav_positions": np.asarray(raw.uav_positions, dtype=np.float64).copy(),
                    "user_positions": np.asarray(raw.user_positions, dtype=np.float64).copy(),
                    "bs_positions": np.asarray(raw.ground_bs_positions, dtype=np.float64).copy(),
                    "current_step": int(raw.current_step), "area": float(raw.area_size),
                    "max_steps": int(raw.max_steps),
                })
                action = rng.uniform(-1, 1, size=(8, 4)).astype(np.float32)
                action[:, 3] = 0.0
                obs, _, _, _, info = env.step(action)
        finally:
            env.close()
    return frames
