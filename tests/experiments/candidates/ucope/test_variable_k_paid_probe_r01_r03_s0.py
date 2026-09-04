from __future__ import annotations

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
    checkpoint,
    native_backend,
    reference_oracle,
)
from experiments.candidates.ucope.variable_k_paid_probe_r01_r03.contract import (
    COMPONENT,
    REGISTERED_MASTER_SEEDS,
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
