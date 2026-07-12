from __future__ import annotations

import random
from types import SimpleNamespace

import numpy as np
import pytest
import torch
from torch import nn

from ha_ctse_process.r27_g2_runtime import (
    REQUIRED_CUBLAS_WORKSPACE_CONFIG,
    RUNTIME_ATTRIBUTE_NAMES,
    R27G2ContractError,
    assert_environment_states_equal,
    assert_environment_rng_states_equal,
    assert_global_rng_states_equal,
    assert_runtime_matches_snapshot,
    capture_environment_state,
    capture_environment_rng_state,
    capture_global_rng_state,
    capture_module_state,
    capture_runtime_snapshot,
    capture_structured_evidence,
    capture_value_norm_payload,
    capture_value_norm_state,
    configure_deterministic_cuda,
    environment_states_equal,
    environment_rng_states_equal,
    global_rng_states_equal,
    module_state_differences,
    module_states_equal,
    restore_runtime_snapshot,
    runtime_snapshot_differences,
    runtime_snapshots_equal,
    typed_evidence_equal,
    value_norm_states_equal,
)


EXPECTED_RUNTIME_ATTRIBUTES = (
    "active_skills",
    "active_duration_indices",
    "duration_remaining",
    "skill_age",
    "has_active_skill",
    "active_team_codes",
    "team_intent_remaining",
    "team_intent_age",
    "low_actor_hxs",
    "low_critic_hxs",
    "_last_low_context",
    "segments",
    "situation_debouncer",
    "per_agent_situation_debouncer",
    "situation_hazard_guard",
    "_last_situation_state",
    "_last_agent_situation_state",
    "_team_transition_open",
    "_team_transition_closed",
    "_team_transition_env_steps",
    "_team_intent_boundary_count",
    "_team_intent_boundary_trunc_fracs",
    "_team_intent_boundary_trunc_by_duration",
    "_team_intent_dwell_checks",
    "_team_intent_age_check_samples",
    "_situation_diag_events",
    "_agent_situation_diag_events",
    "_situation_hazard_forced_renewals",
    "_situation_hazard_events",
)


def _runtime() -> SimpleNamespace:
    values = {
        name: {"name": name, "values": [index, index + 1]}
        for index, name in enumerate(RUNTIME_ATTRIBUTE_NAMES)
    }
    values.update(
        active_skills=np.arange(6, dtype=np.int64).reshape(1, 6),
        active_duration_indices=np.zeros((1, 6), dtype=np.int64),
        duration_remaining=np.full((1, 6), 10, dtype=np.int64),
        skill_age=np.arange(6, dtype=np.int64).reshape(1, 6),
        has_active_skill=np.ones((1, 6), dtype=np.bool_),
        active_team_codes=np.asarray([2], dtype=np.int64),
        team_intent_remaining=np.asarray([20], dtype=np.int64),
        team_intent_age=np.asarray([3], dtype=np.int64),
        low_actor_hxs=np.ones((1, 6, 8), dtype=np.float32),
        low_critic_hxs=np.full((1, 6, 8), 2.0, dtype=np.float32),
        _last_low_context=[{"obs": np.arange(3, dtype=np.float32)}],
        _team_intent_boundary_trunc_by_duration={10: [0.25], 20: [0.5]},
    )
    shared = SimpleNamespace(counter=3, nested={"rows": [1, 2]})
    values["situation_debouncer"] = shared
    values["per_agent_situation_debouncer"] = shared
    return SimpleNamespace(**values)


def test_registered_runtime_inventory_is_exact() -> None:
    assert RUNTIME_ATTRIBUTE_NAMES == EXPECTED_RUNTIME_ATTRIBUTES
    assert len(RUNTIME_ATTRIBUTE_NAMES) == 29
    assert len(set(RUNTIME_ATTRIBUTE_NAMES)) == len(RUNTIME_ATTRIBUTE_NAMES)


def test_runtime_snapshot_is_deep_restorable_and_branch_isolated() -> None:
    source = _runtime()
    canonical = capture_runtime_snapshot(source)
    assert tuple(canonical) == RUNTIME_ATTRIBUTE_NAMES

    source.active_skills[0, 0] = 99
    source.situation_debouncer.nested["rows"].append(9)
    assert canonical["active_skills"][0, 0] == 0
    assert canonical["situation_debouncer"].nested["rows"] == [1, 2]

    branch_a = _runtime()
    branch_b = _runtime()
    restore_runtime_snapshot(branch_a, canonical)
    restore_runtime_snapshot(branch_b, canonical)
    assert branch_a.situation_debouncer is branch_a.per_agent_situation_debouncer
    assert branch_b.situation_debouncer is branch_b.per_agent_situation_debouncer
    assert branch_a.situation_debouncer is not branch_b.situation_debouncer
    assert_runtime_matches_snapshot(branch_a, canonical)
    assert_runtime_matches_snapshot(branch_b, canonical)

    branch_a.duration_remaining[0, 0] -= 1
    assert branch_b.duration_remaining[0, 0] == 10
    assert canonical["duration_remaining"][0, 0] == 10
    recaptured_a = capture_runtime_snapshot(branch_a)
    assert runtime_snapshot_differences(recaptured_a, canonical) == (
        "duration_remaining",
    )
    assert not runtime_snapshots_equal(recaptured_a, canonical)
    assert runtime_snapshots_equal(capture_runtime_snapshot(branch_b), canonical)


def test_runtime_snapshot_fails_closed_for_missing_or_reordered_inventory() -> None:
    runtime = _runtime()
    del runtime._situation_hazard_events
    with pytest.raises(R27G2ContractError, match="missing registered attributes"):
        capture_runtime_snapshot(runtime)

    snapshot = capture_runtime_snapshot(_runtime())
    reordered = dict(reversed(tuple(snapshot.items())))
    with pytest.raises(R27G2ContractError, match="inventory mismatch"):
        restore_runtime_snapshot(_runtime(), reordered)


def test_structured_evidence_is_typed_order_independent_and_fail_closed() -> None:
    left = {"b": np.asarray([1.0, -0.0], dtype=np.float32), "a": (1, True)}
    right = {"a": (1, True), "b": np.asarray([1.0, -0.0], dtype=np.float32)}
    assert typed_evidence_equal(left, right)
    assert not typed_evidence_equal(1, np.int64(1))
    assert not typed_evidence_equal(-0.0, 0.0)
    with pytest.raises(R27G2ContractError, match="unsupported canonical evidence type"):
        capture_structured_evidence(object())


class _FakeRenderer:
    def __init__(self) -> None:
        self.unstable_frame_counter = 0


class _UnderlyingEnvironment:
    def __init__(self, seed: int) -> None:
        self.scalar = 7
        self.array = np.arange(6, dtype=np.float32).reshape(2, 3)
        self.mapping = {"z": {3, 1, 2}, "a": [True, None]}
        self.random_state = np.random.RandomState(seed)
        self.renderer = _FakeRenderer()
        self.callback = lambda value: value
        self.self_cycle = self


class _Adapter:
    def __init__(self, seed: int) -> None:
        self.env = _UnderlyingEnvironment(seed)
        self.generator = np.random.default_rng(seed + 100)
        self.adapter_count = 5


def test_environment_state_covers_graph_cycles_and_type_based_exclusions() -> None:
    first = _Adapter(11)
    second = _Adapter(11)
    state_first = capture_environment_state(first, first.env)
    state_second = capture_environment_state(second, second.env)
    assert environment_states_equal(state_first, state_second)
    assert any(entry.type_name == "cycle-reference" for entry in state_first.entries)
    assert any(".scalar<" in entry.path for entry in state_first.entries)
    assert not any("random_state" in entry.path for entry in state_first.entries)
    assert not any("generator" in entry.path for entry in state_first.entries)
    assert not any("renderer" in entry.path for entry in state_first.entries)
    assert not any("callback" in entry.path for entry in state_first.entries)

    first.env.random_state.rand()
    first.generator.random()
    first.env.renderer.unstable_frame_counter += 10
    first.env.another_renderer_handle = _FakeRenderer()
    assert_environment_states_equal(
        capture_environment_state(first, first.env), state_second
    )

    first.env.array[0, 0] = 99.0
    with pytest.raises(R27G2ContractError, match="environment state mismatch"):
        assert_environment_states_equal(
            capture_environment_state(first, first.env), state_second
        )


def test_environment_rng_capture_is_separate_and_exact() -> None:
    scenario_a = np.random.RandomState(3)
    scenario_b = np.random.RandomState(3)
    adapter_a = np.random.default_rng(9)
    adapter_b = np.random.default_rng(9)
    first = capture_environment_rng_state(scenario_a, adapter_a)
    second = capture_environment_rng_state(scenario_b, adapter_b)
    assert environment_rng_states_equal(first, second)
    assert_environment_rng_states_equal(first, second)

    scenario_a.rand()
    advanced = capture_environment_rng_state(scenario_a, adapter_a)
    assert not environment_rng_states_equal(advanced, second)
    with pytest.raises(R27G2ContractError, match="environment RNG state mismatch"):
        assert_environment_rng_states_equal(advanced, second)

    with pytest.raises(R27G2ContractError, match="RandomState"):
        capture_environment_rng_state(np.random.default_rng(1), adapter_a)  # type: ignore[arg-type]
    with pytest.raises(R27G2ContractError, match="Generator"):
        capture_environment_rng_state(scenario_b, np.random.RandomState(1))  # type: ignore[arg-type]

    wrapped = SimpleNamespace(
        env=SimpleNamespace(np_random=np.random.RandomState(3)),
        np_random=np.random.default_rng(9),
    )
    assert environment_rng_states_equal(
        capture_environment_rng_state(wrapped), second
    )


def test_global_rng_capture_detects_consumption_without_cuda() -> None:
    python_state = random.getstate()
    numpy_state = np.random.get_state()
    torch_state = torch.get_rng_state()
    try:
        before = capture_global_rng_state(require_cuda=False, include_cuda=False)
        same = capture_global_rng_state(require_cuda=False, include_cuda=False)
        assert global_rng_states_equal(before, same)
        random.random()
        np.random.random()
        torch.rand(1)
        after = capture_global_rng_state(require_cuda=False, include_cuda=False)
        assert not global_rng_states_equal(before, after)
        with pytest.raises(R27G2ContractError, match="global RNG state mismatch"):
            assert_global_rng_states_equal(before, after)
    finally:
        random.setstate(python_state)
        np.random.set_state(numpy_state)
        torch.set_rng_state(torch_state)


class _BufferedModule(nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.linear = nn.Linear(2, 2)
        self.register_buffer("running", torch.tensor([1.0, 2.0]))
        self.register_buffer("updates", torch.tensor(0, dtype=torch.int64))


def test_module_state_includes_parameters_buffers_and_agent_modules() -> None:
    torch_state = torch.get_rng_state()
    try:
        torch.manual_seed(4)
        module = _BufferedModule()
        original = capture_module_state(module)
        assert module_states_equal(original, capture_module_state(module))
        with torch.no_grad():
            module.running[0] += 1.0
        changed = capture_module_state(module)
        assert not module_states_equal(changed, original)
        assert module_state_differences(changed, original) == ("module.running",)
        with torch.no_grad():
            module.running[0] -= 1.0
        assert module_states_equal(capture_module_state(module), original)
        with torch.no_grad():
            module.linear.weight[0, 0] += 1.0
        assert not module_states_equal(capture_module_state(module), original)

        other = _BufferedModule()
        agent = SimpleNamespace(z_module=module, a_module=other, alias=other, note="x")
        agent_state = capture_module_state(agent)
        with torch.no_grad():
            other.running[1] += 1.0
        assert not module_states_equal(capture_module_state(agent), agent_state)
        with pytest.raises(R27G2ContractError, match="no direct"):
            capture_module_state(SimpleNamespace(value=1))
    finally:
        torch.set_rng_state(torch_state)


def test_value_norm_state_covers_non_module_critic_scaling_state() -> None:
    class FakeNorm:
        def __init__(self, mean: float) -> None:
            self.mean = mean

        def state_dict(self):
            return {"mean": self.mean, "var": 2.0, "count": 9.0}

    agent = SimpleNamespace(
        high_value_norm=FakeNorm(1.0),
        low_value_norm=FakeNorm(3.0),
    )
    before = capture_value_norm_state(agent)
    checkpoint_state = capture_value_norm_payload(
        {
            "high_value_norm": agent.high_value_norm.state_dict(),
            "low_value_norm": agent.low_value_norm.state_dict(),
        }
    )
    assert value_norm_states_equal(before, checkpoint_state)
    agent.low_value_norm.mean = 4.0
    assert not value_norm_states_equal(capture_value_norm_state(agent), before)


def test_deterministic_cuda_setup_rejects_cpu_unavailable_and_late_cublas(
    monkeypatch,
) -> None:
    monkeypatch.delenv("CUBLAS_WORKSPACE_CONFIG", raising=False)
    monkeypatch.setattr(torch.cuda, "is_initialized", lambda: False)
    monkeypatch.setattr(torch.cuda, "is_available", lambda: False)
    with pytest.raises(R27G2ContractError, match="CPU fallback is forbidden"):
        configure_deterministic_cuda("cpu")
    with pytest.raises(R27G2ContractError, match="CUDA unavailable"):
        configure_deterministic_cuda("cuda")
    assert os_environ_cublas() == REQUIRED_CUBLAS_WORKSPACE_CONFIG

    monkeypatch.delenv("CUBLAS_WORKSPACE_CONFIG", raising=False)
    monkeypatch.setattr(torch.cuda, "is_initialized", lambda: True)
    with pytest.raises(R27G2ContractError, match="before CUDA initialization"):
        configure_deterministic_cuda("cuda")


def os_environ_cublas() -> str | None:
    # Kept as a tiny function so tests cannot accidentally cache environment state.
    import os

    return os.environ.get("CUBLAS_WORKSPACE_CONFIG")


def test_deterministic_cuda_setup_applies_registered_backend_flags(monkeypatch) -> None:
    old_deterministic = torch.are_deterministic_algorithms_enabled()
    old_warn_only = torch.is_deterministic_algorithms_warn_only_enabled()
    old_cudnn_deterministic = torch.backends.cudnn.deterministic
    old_cudnn_benchmark = torch.backends.cudnn.benchmark
    old_matmul_tf32 = torch.backends.cuda.matmul.allow_tf32
    old_cudnn_tf32 = torch.backends.cudnn.allow_tf32
    monkeypatch.setenv("CUBLAS_WORKSPACE_CONFIG", REQUIRED_CUBLAS_WORKSPACE_CONFIG)
    monkeypatch.setattr(torch.cuda, "is_initialized", lambda: False)
    monkeypatch.setattr(torch.cuda, "is_available", lambda: True)
    monkeypatch.setattr(torch.cuda, "device_count", lambda: 1)
    try:
        contract = configure_deterministic_cuda("cuda:0")
        assert contract.device == "cuda:0"
        assert contract.cublas_workspace_config == REQUIRED_CUBLAS_WORKSPACE_CONFIG
        assert contract.deterministic_algorithms
        assert contract.cudnn_deterministic
        assert not contract.cudnn_benchmark
        assert not contract.cuda_matmul_allow_tf32
        assert not contract.cudnn_allow_tf32
    finally:
        torch.use_deterministic_algorithms(old_deterministic, warn_only=old_warn_only)
        torch.backends.cudnn.deterministic = old_cudnn_deterministic
        torch.backends.cudnn.benchmark = old_cudnn_benchmark
        torch.backends.cuda.matmul.allow_tf32 = old_matmul_tf32
        torch.backends.cudnn.allow_tf32 = old_cudnn_tf32
