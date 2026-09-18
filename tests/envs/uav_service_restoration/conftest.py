"""Shared fixtures for the ``uav_service_restoration_v0`` tests.

Generated files go through ``tmp_path``; nothing is written next to the sources.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from envs.uav_service_restoration import config_from_dict, config_to_dict, load_config
from envs.uav_service_restoration.config import EnvConfig

REPO_ROOT = Path(__file__).resolve().parents[3]
SMOKE_CONFIG_PATH = REPO_ROOT / "configs" / "uav_service_restoration" / "smoke_fixture.json"
FIXTURE_ROOT = REPO_ROOT / "tests" / "fixtures" / "uav_service_restoration"
MILAN_SAMPLE = FIXTURE_ROOT / "milan_shaped_sample"


@pytest.fixture(scope="session")
def smoke_config() -> EnvConfig:
    return load_config(SMOKE_CONFIG_PATH)


@pytest.fixture
def config_doc() -> dict:
    """A mutable copy of the smoke configuration document."""

    return config_to_dict(load_config(SMOKE_CONFIG_PATH))


def rebuild(doc: dict, **_unused) -> EnvConfig:
    return config_from_dict(doc)


@pytest.fixture
def short_config(config_doc: dict) -> EnvConfig:
    """A four-step episode, so lifecycle tests stay fast."""

    config_doc["episode"]["duration_s"] = 40.0
    return config_from_dict(config_doc)


@pytest.fixture(scope="session")
def repo_root() -> Path:
    return REPO_ROOT


@pytest.fixture(scope="session")
def milan_sample_dir() -> Path:
    return MILAN_SAMPLE


@pytest.fixture(scope="session")
def preset_dir() -> Path:
    return REPO_ROOT / "configs" / "uav_service_restoration"


@pytest.fixture(scope="session")
def legacy_fingerprint_dir() -> Path:
    return FIXTURE_ROOT / "legacy_fingerprints"


@pytest.fixture
def rng() -> np.random.Generator:
    return np.random.default_rng(12345)
