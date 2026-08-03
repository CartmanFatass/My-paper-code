"""Focused ownership and wiring checks for the extracted standalone CLI."""

from __future__ import annotations

import ast
from pathlib import Path
import sys
from types import SimpleNamespace

import numpy as np
import pytest

from ha_ctse_process import standalone_cli
from ha_ctse_process import train
from ha_ctse_process import eval_checkpoints
from ha_ctse_process import export_substrate_gate


HELPER_NAMES = {
    "load_config",
    "parse_args",
    "parse_int_tuple",
    "apply_standalone_overrides",
    "resolve_device",
    "create_env",
    "create_envs",
    "create_collector",
    "action_space_details",
    "create_agent",
}


def test_standalone_cli_is_the_sole_helper_owner_and_callers_bind_directly():
    train_tree = ast.parse(Path(train.__file__).read_text(encoding="utf-8"))
    train_definitions = {
        node.name for node in train_tree.body if isinstance(node, ast.FunctionDef)
    }

    assert not (HELPER_NAMES & train_definitions)
    for name in {
        "load_config",
        "parse_args",
        "apply_standalone_overrides",
        "create_env",
    }:
        assert getattr(train, name) is getattr(standalone_cli, name)
    for name in HELPER_NAMES - {
        "load_config",
        "parse_args",
        "apply_standalone_overrides",
        "create_env",
    }:
        assert not hasattr(train, name)

    assert eval_checkpoints.create_env is standalone_cli.create_env
    helpers = export_substrate_gate._train_helpers()
    assert helpers.create_agent is standalone_cli.create_agent
    assert helpers.load_config is standalone_cli.load_config


def test_parse_args_preserves_defaults_and_options(monkeypatch):
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "standalone",
            "--mode",
            "eval",
            "--config",
            "test_config",
            "--preset",
            "tiny",
            "--scenario",
            "sc7",
            "--seed",
            "17",
            "--num_envs",
            "3",
            "--collector_backend",
            "subproc",
            "--collector_start_method",
            "fork",
            "--device",
            "cpu",
        ],
    )

    args = standalone_cli.parse_args()

    assert args.mode == "eval"
    assert args.config == "test_config"
    assert args.preset == "tiny"
    assert args.scenario == "sc7"
    assert args.seed == 17
    assert args.num_envs == 3
    assert args.collector_backend == "subproc"
    assert args.collector_start_method == "fork"
    assert args.device == "cpu"
    assert args.total_timesteps == 320000
    assert args.rollout_length == 500
    assert args.skill_interval == 10
    assert args.infrastructure_profile_interval == 0


def test_infrastructure_profile_interval_accepts_positive_and_rejects_negative(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["standalone", "--infrastructure-profile-interval", "7"])
    assert standalone_cli.parse_args().infrastructure_profile_interval == 7

    monkeypatch.setattr(sys, "argv", ["standalone", "--infrastructure-profile-interval", "-1"])
    with pytest.raises(SystemExit):
        standalone_cli.parse_args()


def test_config_override_and_environment_wiring_use_cheap_mocks(monkeypatch):
    created = []

    class Config:
        def __init__(self, preset=None):
            self.preset = preset

    fake_module = SimpleNamespace(Config=Config)
    monkeypatch.setattr(standalone_cli.importlib, "import_module", lambda name: fake_module)
    config = standalone_cli.load_config("test_config", "small")
    assert config.preset == "small"

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "standalone",
            "--scenario",
            "energy",
            "--n_agents",
            "4",
            "--skill_lifetime_candidates",
            "3; 5",
            "--team_bridge_type",
            "deterministic",
        ],
    )
    args = standalone_cli.parse_args()
    standalone_cli.apply_standalone_overrides(config, args)
    assert config.n_agents == 4
    assert config.n_uavs == 4
    assert config.skill_lifetime_candidates == (3, 5)
    assert config.team_bridge_type == "deterministic"

    sentinel = object()

    def fake_make_env(received_config, spec):
        created.append((received_config, spec))
        return lambda: sentinel

    monkeypatch.setattr(standalone_cli, "make_env", fake_make_env)
    assert standalone_cli.create_env(config, "energy", seed=23, rank=2, scale_mode="eval") is sentinel
    received_config, spec = created.pop()
    assert received_config is config
    assert (spec.seed, spec.rank, spec.scale_mode) == (23, 2, "eval")


def test_device_and_action_space_wiring_without_runtime_env(monkeypatch):
    monkeypatch.setattr(standalone_cli.torch.cuda, "is_available", lambda: False)
    assert standalone_cli.resolve_device("cuda") == "cpu"
    assert standalone_cli.resolve_device("cpu") == "cpu"

    continuous_env = SimpleNamespace(
        action_space=SimpleNamespace(
            dtype=np.dtype(np.float32),
            low=np.array([-2.0], dtype=np.float32),
            high=np.array([2.0], dtype=np.float32),
        )
    )
    assert standalone_cli.action_space_details(continuous_env) == (
        "continuous",
        -2.0,
        2.0,
    )
