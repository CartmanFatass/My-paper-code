"""Shared fixtures for energy_relay_benchmark B01 tests (tiny, CPU)."""

from __future__ import annotations

import numpy as np
import pytest
import torch

from experiments.candidates.energy_relay_benchmark.b01.evaluation import make_eval_config
from experiments.candidates.uav_service_auxiliary.b01.native import make_env, seed_everything
from hmasd.agent import HMASDAgent

POLICY_SEED = 925031


@pytest.fixture(scope="session")
def config_60():
    return make_eval_config(60, POLICY_SEED)


@pytest.fixture(scope="session")
def fresh_checkpoint(tmp_path_factory, config_60):
    """A freshly initialised (untrained) HMASD agent saved like a B09 endpoint."""
    root = tmp_path_factory.mktemp("fresh_agent")
    seed_everything(POLICY_SEED, torch.device("cpu"))
    agent = HMASDAgent(config_60, log_dir=str(root / "logs"), device=torch.device("cpu"))
    path = root / "agent.pt"
    agent.save_model(path)
    return path


@pytest.fixture(scope="session")
def live_frames(config_60):
    """Real (8, 365) legal observations from two worlds under random bounded actions."""
    rng = np.random.default_rng(20260926)
    frames = []
    for seed in (952001, 953001):
        env = make_env(config_60, seed)
        try:
            obs, _ = env.reset(seed=seed)
            frames.append(np.asarray(obs, dtype=np.float32))
            for _ in range(24):
                action = rng.uniform(-1, 1, size=(8, 4)).astype(np.float32)
                action[:, 3] = 0.0
                obs, *_ = env.step(action)
                frames.append(np.asarray(obs, dtype=np.float32))
        finally:
            env.close()
    return frames
