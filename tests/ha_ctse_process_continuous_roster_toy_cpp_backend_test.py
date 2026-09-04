from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from contextlib import contextmanager
import hashlib
import os

import numpy as np
import pytest

from ha_ctse_process import continuous_roster_random_process_g34 as g34
from ha_ctse_process import continuous_roster_six_coordinate_cs_g38 as g38
from envs.continuous_roster import cpp_backend as cpp
from envs.continuous_roster import runtime_capacity as roster_env
from tools.benchmarks import benchmark_continuous_roster_toy_cpp_backend as benchmark


@pytest.mark.parametrize("capacity", g34.CAPACITIES)
@pytest.mark.parametrize("process_kind", ("fixed", "random"))
def test_native_batch_is_bitwise_equal_across_lifecycle_processes(
    capacity: int, process_kind: str
) -> None:
    processes = g34.make_process_ledgers(
        replicate=0, capacity=capacity, episode_count=4
    )
    reference = tuple(
        g34.RandomProcessRosterEnv(row)
        if process_kind == "random"
        else roster_env.RuntimeCapacityRosterEnv(row.base)
        for row in processes
    )
    accelerated = tuple(
        g34.RandomProcessRosterEnv(row)
        if process_kind == "random"
        else roster_env.RuntimeCapacityRosterEnv(row.base)
        for row in processes
    )
    batch = cpp.ContinuousRosterToyBatch(accelerated)
    noise = roster_env.make_action_noise(
        (row.episode_id for row in processes),
        action_seed=10_996_000,
        member_capacity=capacity,
    )

    for time in range(roster_env.HORIZON):
        expected_views = tuple(
            g38.observe_g38_actor_source(env, input_mode=g38.FOLD6_INPUT)
            for env in reference
        )
        actual_views = batch.observe_six()
        for expected, actual in zip(expected_views, actual_views):
            assert actual.membership_change == expected.membership_change
            assert np.array_equal(actual.active_mask, expected.active_mask)
            assert np.array_equal(actual.observations, expected.observations)
            assert np.array_equal(actual.critic_state, expected.critic_state)
            assert actual.load == expected.load
            assert actual.target_mix == expected.target_mix

        actions = np.tanh(noise[time]).astype(np.float32)
        actions[~np.stack([view.active_mask for view in expected_views])] = 0.0
        expected_rewards = np.asarray(
            [
                g38.advance_g38_environment(env, view, action)
                for env, view, action in zip(reference, expected_views, actions)
            ],
            dtype=np.float64,
        )
        actual_rewards = batch.advance(
            actual_views, np.ascontiguousarray(actions)
        )
        assert np.array_equal(actual_rewards, expected_rewards)
        for expected, actual in zip(reference, accelerated):
            assert expected.time == actual.time
            assert expected._change == actual._change
            assert expected._terminated == actual._terminated
            assert np.array_equal(expected.active, actual.active)
            assert np.array_equal(expected.age, actual.age)
            assert np.array_equal(expected.previous_actions, actual.previous_actions)

    assert tuple(env.outcome() for env in accelerated) == tuple(
        env.outcome() for env in reference
    )


def test_python_boundary_rejects_invalid_native_inputs_before_execution() -> None:
    capabilities = np.ones((1, 2, 2), dtype=np.float32)
    active = np.asarray(((True, False),), dtype=np.bool_)
    loads = np.asarray((0.5,), dtype=np.float32)
    mixes = np.asarray((0.5,), dtype=np.float32)
    actions = np.zeros((1, 2, 2), dtype=np.float32)

    with pytest.raises(TypeError, match="dtype float32"):
        cpp.reward_batch(
            capabilities=capabilities.astype(np.float64),
            active_mask=active,
            actions=actions,
            loads=loads,
            target_mixes=mixes,
        )
    with pytest.raises(ValueError, match="C-contiguous"):
        cpp.reward_batch(
            capabilities=capabilities[:, ::-1],
            active_mask=active,
            actions=actions,
            loads=loads,
            target_mixes=mixes,
        )
    actions[0, 1, 0] = np.float32(0.25)
    with pytest.raises(ValueError, match="inactive actions"):
        cpp.reward_batch(
            capabilities=capabilities,
            active_mask=active,
            actions=actions,
            loads=loads,
            target_mixes=mixes,
        )


def test_python_boundary_rejects_malformed_native_outputs(monkeypatch: pytest.MonkeyPatch) -> None:
    capabilities = np.ones((1, 2, 2), dtype=np.float32)
    priorities = np.ones((1, 2), dtype=np.float32)
    active = np.asarray(((True, False),), dtype=np.bool_)
    loads = np.asarray((0.5,), dtype=np.float32)
    mixes = np.asarray((0.5,), dtype=np.float32)
    logs = np.asarray((np.log(2.0),), dtype=np.float32)
    malformed = SimpleNamespace(
        observe_six_batch=lambda *_args: (
            np.ones((1, 2, 6), dtype=np.float32),
            np.ones((1, 6), dtype=np.float32),
        )
    )
    monkeypatch.setattr(
        cpp, "load_continuous_roster_toy_cpp_backend", lambda: malformed
    )
    with pytest.raises(RuntimeError, match="inactive member"):
        cpp.observe_six_batch(
            capabilities=capabilities,
            priorities=priorities,
            loads=loads,
            target_mixes=mixes,
            active_mask=active,
            log_counts=logs,
            time_fraction=np.float32(0.0),
        )


def test_native_loader_reuses_the_source_keyed_cpu_module() -> None:
    first = cpp.load_continuous_roster_toy_cpp_backend()
    second = cpp.load_continuous_roster_toy_cpp_backend()
    assert first is second
    assert first.__name__.startswith("hmasd_continuous_roster_toy_")


def test_native_loader_stages_the_exact_continuous_roster_source() -> None:
    module = cpp.load_continuous_roster_toy_cpp_backend()
    staged_source = (
        Path(module.__file__).resolve().parent / "continuous_roster_toy_backend.cpp"
    )
    assert staged_source.read_bytes() == cpp._SOURCE.read_bytes()


def test_process_cache_skips_repeated_toolchain_activation_and_invalidates_source(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    source = tmp_path / "toy.cpp"
    source.write_bytes(b"// v1\n")
    calls: list[str] = []

    @contextmanager
    def toolchain():
        calls.append("toolchain")
        yield

    def build_identity() -> str:
        return hashlib.sha256(source.read_bytes()).hexdigest()[:20]

    def load(**_kwargs):
        calls.append("load")
        return SimpleNamespace(__name__=f"module_{len(calls)}")

    monkeypatch.setattr(cpp, "_SOURCE", source)
    monkeypatch.setattr(cpp, "_LOADED_BACKENDS", {})
    monkeypatch.setattr(cpp, "_windows_toolchain_environment", toolchain)
    monkeypatch.setattr(cpp, "_build_identity", build_identity)
    monkeypatch.setattr(cpp, "load_source_keyed_extension", load)

    first = cpp.load_continuous_roster_toy_cpp_backend(build_root=tmp_path / "build")
    second = cpp.load_continuous_roster_toy_cpp_backend(build_root=tmp_path / "build")
    assert first is second
    assert calls == ["toolchain", "load"]

    source.write_bytes(b"// v2\n")
    third = cpp.load_continuous_roster_toy_cpp_backend(build_root=tmp_path / "build")
    assert third is not first
    assert calls == ["toolchain", "load", "toolchain", "load"]

    fourth = cpp.load_continuous_roster_toy_cpp_backend(
        build_root=tmp_path / "other-build"
    )
    assert fourth is not third
    assert calls == [
        "toolchain", "load", "toolchain", "load", "toolchain", "load"
    ]


def test_build_identity_rechecks_source_bytes_in_same_process(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    source = tmp_path / "mutable_toy.cpp"
    source.write_bytes(b"// first source\n")
    monkeypatch.setattr(cpp, "_SOURCE", source)
    monkeypatch.setattr(cpp.shutil, "which", lambda _name: cpp.sys.executable)
    first = cpp._build_identity()
    source.write_bytes(b"// second source\n")
    second = cpp._build_identity()
    assert first != second


def test_windows_toolchain_context_restores_complete_environment_on_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(cpp.os, "name", "nt")
    monkeypatch.setattr(cpp.shutil, "which", lambda _name: "C:/registered/tool.exe")
    monkeypatch.setenv("VSCMD_ARG_TGT_ARCH", "x64")
    before = dict(os.environ)

    with pytest.raises(RuntimeError, match="probe"):
        with cpp._windows_toolchain_environment():
            os.environ["PATH"] = "C:/temporary/toolchain"
            os.environ["HMASD_TEMP_ACTIVATION"] = "temporary"
            raise RuntimeError("probe")

    assert dict(os.environ) == before


def test_benchmark_schema_is_bounded_and_oracle_gated() -> None:
    result = benchmark.run_benchmark(batch_size=2, capacity=8, repeats=1)
    assert result["schema"] == "continuous_roster_toy_cpp_benchmark_v1"
    assert result["cpu_only"] is True
    assert result["bitwise_outcome_oracle"] is True
    assert result["batch_size"] == 2
    assert result["capacity"] == 8
    assert result["horizon"] == 48
    assert result["repeats"] == 1
    assert result["python_median_seconds"] > 0.0
    assert result["native_median_seconds"] > 0.0
    assert result["speedup"] > 0.0


def test_benchmark_matrix_covers_required_batch_widths(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        benchmark.cpp,
        "load_continuous_roster_toy_cpp_backend",
        lambda: SimpleNamespace(),
    )
    monkeypatch.setattr(
        benchmark,
        "run_benchmark",
        lambda *, batch_size, capacity, repeats: {
            "batch_size": batch_size,
            "capacity": capacity,
            "repeats": repeats,
            "bitwise_outcome_oracle": True,
        },
    )
    result = benchmark.run_benchmark_matrix(
        batch_sizes=(1, 8, 32), capacity=8, repeats=5
    )
    assert result["schema"] == "continuous_roster_toy_cpp_batch_matrix_v2"
    assert result["batch_sizes"] == [1, 8, 32]
    assert result["full_reset_to_terminal_episode"] is True
    assert result["steady_measurement_excludes_process_cold_preflight"] is True
    assert [row["batch_size"] for row in result["results"]] == [1, 8, 32]
