from __future__ import annotations

import ctypes
import json

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import pytest

from envs.native.production_backend import (
    ProductionBackendUnsupported,
    backend_capability,
    require_cpp_batched_production,
)
from experiments.candidates.ucope.variable_k_paid_probe_r01_r03 import (
    benchmark,
    checkpoint,
    native_backend,
    reference_oracle,
)
from experiments.candidates.ucope.variable_k_paid_probe_r01_r03.contract import (
    BASELINE_FEATURES,
    COMPONENT,
    REGISTERED_MASTER_SEEDS,
    ROOT_ACTION_COUNT,
    SCORER_FEATURES,
    SUPPORTED_BATCH_WIDTHS,
    TEST_NAMESPACE,
    TEST_SEEDS,
    require_test_namespace,
)
from experiments.candidates.ucope.variable_k_paid_probe_r01_r03.s0_coupon import (
    run_retained_coupon,
)


def test_firewall_and_shared_registry_fail_closed() -> None:
    for seed in REGISTERED_MASTER_SEEDS:
        with pytest.raises(PermissionError):
            require_test_namespace(TEST_NAMESPACE, seed)
    with pytest.raises(PermissionError):
        require_test_namespace("PRODUCTION", TEST_SEEDS[0])
    capability = backend_capability(COMPONENT)
    assert capability.full_reset_step_cpp is True
    assert capability.supported_batch_widths == SUPPORTED_BATCH_WIDTHS
    assert capability.reference_backend == "test_only_python_scalar_oracle"
    preflight = require_cpp_batched_production(COMPONENT, backend="cpp", batch_width=8)
    assert preflight["python_fallback"] is False
    assert preflight["full_reset_step_cpp"] is True
    with pytest.raises(ProductionBackendUnsupported):
        require_cpp_batched_production(COMPONENT, backend="cpp", batch_width=16)
    with pytest.raises(ProductionBackendUnsupported):
        require_cpp_batched_production(COMPONENT, backend="python", batch_width=8)


def test_all_counter_namespaces_match_scalar_oracle() -> None:
    seed = TEST_SEEDS[0]
    coordinates = (
        (1, 0, 255, 0, 7, 31),
        (2, 1, 255, 0, 258, 5),
        (3, 2, 255, 0, 258, 5),
        (4, 0, 255, 0, 258, 9),
        (5, 1, 2, 0, 258, 1),
        (6, 2, 255, 1, 5000, 1),
    )
    for tag, panel, arm, network, first, second in coordinates:
        assert native_backend.philox_word0(
            seed, tag, panel, arm, network, first, second
        ) == reference_oracle.philox_word0(
            seed, tag, panel, arm, network, first, second
        )


@pytest.mark.parametrize("panel", (0, 1, 2))
def test_native_reset_probe_tail_terminal_matches_test_oracle(panel: int) -> None:
    seed = TEST_SEEDS[0]
    arms = np.asarray((0, 1, 2, 0, 1, 2, 0, 1), dtype=np.int32)
    batch = native_backend.reset_batch(
        seed=seed, panel=panel, batch_index=3, arms=arms
    )
    root_actions = np.zeros(8, dtype=np.int32)
    root = batch.root_step(root_actions)
    tail_actions = np.arange(8, dtype=np.int32) % 5
    tail = batch.tail_step(tail_actions)
    terminal = batch.terminal()
    for slot in range(8):
        oracle = reference_oracle.run_episode(
            seed=seed, panel=panel, batch_index=3, slot=slot, arm=int(arms[slot]),
            root_action=0, tail_action=int(tail_actions[slot]),
        )
        assert np.array_equal(batch.regimes[slot], oracle.regimes)
        assert np.array_equal(batch.root_features[slot], oracle.root_features)
        assert np.array_equal(batch.root_baselines[slot], oracle.root_baseline)
        assert np.array_equal(root["actual_marks"][slot], oracle.actual_marks)
        assert np.array_equal(root["displayed_marks"][slot], oracle.displayed_marks)
        np.testing.assert_allclose(root["probe_components"][slot], oracle.probe_components, rtol=0, atol=1e-7)
        np.testing.assert_allclose(root["tail_features"][slot], oracle.tail_features, rtol=0, atol=1e-7)
        np.testing.assert_allclose(root["tail_baselines"][slot], oracle.tail_baseline, rtol=0, atol=1e-7)
        np.testing.assert_allclose(tail[slot], oracle.components[:3], rtol=0, atol=1e-7)
        np.testing.assert_allclose(terminal["components"][slot], oracle.components, rtol=0, atol=1e-7)
        np.testing.assert_allclose(terminal["totals"][slot], oracle.total, rtol=0, atol=1e-7)
    batch.close()
    with pytest.raises(native_backend.NativeBackendError):
        batch.close()


def test_native_reset_later_invalid_arm_is_failure_atomic() -> None:
    width = 8
    valid_arms = np.arange(width, dtype=np.int32) % 3
    before = native_backend.reset_batch(
        seed=TEST_SEEDS[0], panel=0, batch_index=5, arms=valid_arms
    )
    after: native_backend.NativeBatch | None = None
    try:
        invalid_arms = valid_arms.copy()
        invalid_arms[-1] = 3
        handles = np.full(width, np.uint64(0xA5A5A5A5A5A5A5A5), dtype=np.uint64)
        episodes = np.full(width, np.int64(-101), dtype=np.int64)
        regimes = np.full((width, 3), np.int32(-102), dtype=np.int32)
        root_features = np.full(
            (width, ROOT_ACTION_COUNT, SCORER_FEATURES),
            np.float32(-103.5),
            dtype=np.float32,
        )
        root_baselines = np.full(
            (width, BASELINE_FEATURES), np.float32(-104.5), dtype=np.float32
        )
        outputs = (handles, episodes, regimes, root_features, root_baselines)
        sentinels = tuple(output.copy() for output in outputs)
        library = before.library
        code = int(
            library.ucope_r01_r03_reset_batch(
                TEST_SEEDS[0],
                0,
                6,
                width,
                invalid_arms.ctypes.data_as(ctypes.POINTER(ctypes.c_int32)),
                handles.ctypes.data_as(ctypes.POINTER(ctypes.c_uint64)),
                episodes.ctypes.data_as(ctypes.POINTER(ctypes.c_int64)),
                regimes.ctypes.data_as(ctypes.POINTER(ctypes.c_int32)),
                root_features.ctypes.data_as(ctypes.POINTER(ctypes.c_float)),
                root_baselines.ctypes.data_as(ctypes.POINTER(ctypes.c_float)),
            )
        )

        first_possible_partial_handle = int(before.handles[-1]) + 1
        partial_close_codes = []
        for handle in range(
            first_possible_partial_handle, first_possible_partial_handle + width
        ):
            repeated_handle = np.full(width, np.uint64(handle), dtype=np.uint64)
            partial_close_codes.append(
                int(
                    library.ucope_r01_r03_close_batch(
                        repeated_handle.ctypes.data_as(
                            ctypes.POINTER(ctypes.c_uint64)
                        ),
                        width,
                    )
                )
            )

        after = native_backend.reset_batch(
            seed=TEST_SEEDS[0], panel=0, batch_index=7, arms=valid_arms
        )
        assert code == -2
        assert all(
            np.array_equal(output, sentinel)
            for output, sentinel in zip(outputs, sentinels, strict=True)
        )
        assert partial_close_codes == [-20] * width
        assert np.array_equal(
            after.handles, before.handles + np.uint64(width)
        )
    finally:
        before.close()
        if after is not None:
            after.close()


def test_native_lifecycle_rejects_duplicate_and_malformed_steps() -> None:
    arms = np.zeros(8, dtype=np.int32)
    batch = native_backend.reset_batch(
        seed=TEST_SEEDS[0], panel=0, batch_index=0, arms=arms
    )
    actions = np.zeros(8, dtype=np.int32)
    batch.root_step(actions)
    with pytest.raises(native_backend.NativeBackendError):
        batch.root_step(actions)
    with pytest.raises(TypeError):
        batch.tail_step(actions.astype(np.int64))
    batch.tail_step(actions)
    batch.terminal()
    batch.close()


def test_native_lifecycle_rejects_mixed_panels_without_partial_step() -> None:
    arms = np.zeros(8, dtype=np.int32)
    left = native_backend.reset_batch(
        seed=TEST_SEEDS[0], panel=0, batch_index=0, arms=arms
    )
    right = native_backend.reset_batch(
        seed=TEST_SEEDS[0], panel=1, batch_index=0, arms=arms
    )
    mixed = left.handles.copy()
    mixed[-1] = right.handles[-1]
    original = left.handles
    left.handles = mixed
    with pytest.raises(native_backend.NativeBackendError):
        left.root_step(np.zeros(8, dtype=np.int32))
    left.handles = original
    left.root_step(np.zeros(8, dtype=np.int32))
    left.tail_step(np.zeros(8, dtype=np.int32))
    left.terminal()
    left.close()
    right.root_step(np.zeros(8, dtype=np.int32))
    right.tail_step(np.zeros(8, dtype=np.int32))
    right.terminal()
    right.close()


def test_counter_and_action_order_are_parallel_byte_equal() -> None:
    seed = TEST_SEEDS[1]
    sequential = [native_backend.counter_fill(seed=seed + index, width=768, iterations=500) for index in range(2)]
    with ThreadPoolExecutor(max_workers=2) as pool:
        parallel = list(
            pool.map(
                lambda index: native_backend.counter_fill(
                    seed=seed + index, width=768, iterations=500
                ),
                range(2),
            )
        )
    assert all(np.array_equal(left, right) for left, right in zip(sequential, parallel, strict=True))
    probabilities = np.full((32, 6), np.float32(1.0 / 6.0), dtype=np.float32)
    arms = np.arange(32, dtype=np.int32) % 3
    counts = np.full(32, 6, dtype=np.int32)
    native_actions = native_backend.sample_actions(
        probabilities, seed=seed, panel=2, batch_index=4, arms=arms,
        decision_code=0, legal_counts=counts,
    )
    oracle_actions = np.asarray(
        [
            reference_oracle.sample_action(
                probabilities[row], seed=seed, panel=2, batch_index=4,
                slot=row, arm=int(arms[row]), decision_code=0,
            )
            for row in range(32)
        ],
        dtype=np.int32,
    )
    assert np.array_equal(native_actions, oracle_actions)


@pytest.mark.parametrize(
    "name", ("counter_frontier", "source_sha256", "native_artifact_sha256")
)
@pytest.mark.parametrize(
    "invalid_digest",
    (
        pytest.param(None, id="not-a-string"),
        pytest.param("0" * 63, id="wrong-length"),
        pytest.param("A" * 64, id="uppercase"),
        pytest.param("g" * 64, id="non-hex"),
    ),
)
def test_s0_checkpoint_metadata_requires_lowercase_sha256(
    name: str, invalid_digest: object
) -> None:
    metadata: dict[str, object] = {
        "completed_batch": 0,
        "next_batch": 1,
        "counter_frontier": "0" * 64,
        "batch_width": 768,
        "worker_count": 1,
        "torch_threads": 1,
        "source_sha256": "1" * 64,
        "native_artifact_sha256": "2" * 64,
    }
    checkpoint._validate_metadata(metadata)
    metadata[name] = invalid_digest
    with pytest.raises(ValueError):
        checkpoint._validate_metadata(metadata)


def test_exact_shape_fp32_update_atomic_cold_resume_and_permutation_coupon(tmp_path: Path) -> None:
    record = run_retained_coupon(
        namespace=TEST_NAMESPACE,
        seed=TEST_SEEDS[0],
        panel=0,
        work_root=tmp_path,
    )
    assert record["question_relevant_output"] is False
    assert record["complete_r03_package"] is False
    assert record["registered_seed_used"] is False
    assert record["fp32_hot_path"] is True
    assert record["recurrent_state"] == "NOT_APPLICABLE"
    assert record["initial_pairing_equal"] is True
    assert record["resume"]["byte_equal"] is True
    assert record["resume"]["optimizer_steps"] == [2]
    assert record["resume"]["committed_step_repeated"] is False
    assert record["finite_evaluation_coupon"]["direct_cache_byte_equal"] is True
    checkpoint_path = tmp_path / "ucope_r01_r03_s0.TEST_ONLY.pt"
    assert checkpoint_path.is_file()
    assert checkpoint_path.stat().st_size == record["checkpoint"]["bytes"]


@pytest.mark.parametrize(("gates_pass", "expected_exit"), ((True, 0), (False, 2)))
def test_benchmark_main_s0_dispatch_schema_provenance_and_exit(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    gates_pass: bool,
    expected_exit: int,
) -> None:
    command: dict[str, object] = {
        "interpreter": "fixture-python",
        "module": benchmark.__name__,
    }
    record: dict[str, object] = {
        "schema": benchmark.SCHEMA,
        "command": command,
        "all_s0_gates_pass": gates_pass,
        "measured_resources": {"fixture_only": True},
        "complete_plan_projection": {"fixture_only": True},
    }
    dispatched_workspaces: list[Path] = []

    def run_s0(workspace: Path) -> dict[str, object]:
        dispatched_workspaces.append(workspace)
        return record

    def reject_s1(_workspace: Path) -> dict[str, object]:
        pytest.fail("the retained S0 CLI dispatched the S1 benchmark")

    passed_argv = ["--stage", "s0", "--work-root", str(tmp_path)]
    monkeypatch.setattr(benchmark, "_benchmark", run_s0)
    monkeypatch.setattr(benchmark, "_benchmark_s1", reject_s1)
    monkeypatch.setattr(
        benchmark.sys, "argv", ["ambient-program", "--stage", "s1"]
    )

    assert benchmark.main(passed_argv) == expected_exit
    summary = json.loads(capsys.readouterr().out)
    assert dispatched_workspaces == [tmp_path.resolve()]
    assert record["schema"] == benchmark.SCHEMA
    assert record["stage"] == "s0"
    recorded_command = record["command"]
    assert isinstance(recorded_command, dict)
    assert recorded_command["program"] == "ambient-program"
    assert recorded_command["module"] == benchmark.__name__
    assert recorded_command["stage"] == "s0"
    assert recorded_command["argv"] == ["ambient-program", *passed_argv]
    assert summary["stage"] == "s0"
    assert summary["schema"] == benchmark.SCHEMA
    assert summary["command"] == recorded_command
    assert summary["all_s0_gates_pass"] is gates_pass


@pytest.mark.parametrize("path_kind", ("work_root", "output"))
@pytest.mark.parametrize("symlink_location", ("final", "ancestor"))
def test_benchmark_main_s0_rejects_symlinked_assigned_paths_before_runner(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    path_kind: str,
    symlink_location: str,
) -> None:
    outside = tmp_path / "outside"
    assigned = tmp_path / "assigned"
    outside.mkdir()
    assigned.mkdir()
    leaf_name = "workspace" if path_kind == "work_root" else "evidence.json"

    if symlink_location == "final":
        redirected = outside / leaf_name
        if path_kind == "work_root":
            redirected.mkdir()
            sentinel = redirected / "sentinel.bin"
        else:
            sentinel = redirected
        link = assigned / leaf_name
        supplied_path = link
        link_target = redirected
        link_is_directory = path_kind == "work_root"
    else:
        redirected_parent = outside / "redirected-parent"
        redirected_parent.mkdir()
        redirected = redirected_parent / leaf_name
        if path_kind == "work_root":
            redirected.mkdir()
            sentinel = redirected / "sentinel.bin"
        else:
            sentinel = redirected
        link = assigned / "linked-parent"
        supplied_path = link / leaf_name
        link_target = redirected_parent
        link_is_directory = True

    sentinel_bytes = b"outside-sentinel-must-not-change\n"
    sentinel.write_bytes(sentinel_bytes)
    try:
        link.symlink_to(link_target, target_is_directory=link_is_directory)
    except OSError as error:
        pytest.skip(f"symlink creation unavailable: {error}")

    runner_invocations: list[Path] = []

    def run_s0(workspace: Path) -> dict[str, object]:
        runner_invocations.append(workspace)
        if path_kind == "work_root":
            (workspace / "sentinel.bin").write_bytes(b"runner-followed-symlink\n")
        return {
            "schema": benchmark.SCHEMA,
            "command": {},
            "all_s0_gates_pass": True,
            "measured_resources": {"fixture_only": True},
            "complete_plan_projection": {"fixture_only": True},
        }

    safe_work_root = tmp_path / "safe-workspace"
    work_root = supplied_path if path_kind == "work_root" else safe_work_root
    passed_argv = ["--stage", "s0", "--work-root", str(work_root)]
    if path_kind == "output":
        passed_argv.extend(("--output", str(supplied_path)))
    monkeypatch.setattr(benchmark, "_benchmark", run_s0)

    label = "work root" if path_kind == "work_root" else "output"
    with pytest.raises(
        ValueError,
        match=rf"^{label} path must not contain symlink components$",
    ):
        benchmark.main(passed_argv)
    assert runner_invocations == []
    assert sentinel.read_bytes() == sentinel_bytes


def test_hot_path_contains_no_wider_or_proof_grade_numeric_surface() -> None:
    package = Path(__file__).resolve().parents[4] / "experiments/candidates/ucope/variable_k_paid_probe_r01_r03"
    cpp = (package / "native/ucope_r01_r03_backend.cpp").read_text(encoding="utf-8").lower()
    python_hot = "\n".join(
        (package / name).read_text(encoding="utf-8").lower()
        for name in ("native_backend.py", "model.py", "s0_coupon.py")
    )
    for signature in ("double", "long double", "mpmath", "decimal", "multiprecision"):
        assert signature not in cpp
    for signature in ("torch.float64", "np.float64", "set_default_dtype", "mpmath", "decimal"):
        assert signature not in python_hot
    assert "require_cpp_batched_production(" in (package / "s0_coupon.py").read_text(encoding="utf-8")
    assert "fallback" not in (package / "reference_oracle.py").read_text(encoding="utf-8").lower()
