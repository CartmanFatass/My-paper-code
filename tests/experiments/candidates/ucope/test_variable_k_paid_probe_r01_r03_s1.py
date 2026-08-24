from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
import torch

from experiments.candidates.ucope.variable_k_paid_probe_r01_r03 import (
    checkpoint,
    native_backend,
    reference_oracle,
    training,
)
from experiments.candidates.ucope.variable_k_paid_probe_r01_r03.contract import (
    K_TRAIN,
    REGISTERED_MASTER_SEEDS,
    S1_TEST_NAMESPACE,
    S1_TEST_REQUEST,
    S1_TEST_SEEDS,
    require_s1_test_request,
)
from experiments.candidates.ucope.variable_k_paid_probe_r01_r03.model import (
    make_paired_bundles,
)


def test_s1_firewall_rejects_registered_non_test_and_result_requests() -> None:
    require_s1_test_request(S1_TEST_NAMESPACE, S1_TEST_SEEDS[0], S1_TEST_REQUEST)
    for seed in REGISTERED_MASTER_SEEDS:
        with pytest.raises(PermissionError):
            require_s1_test_request(S1_TEST_NAMESPACE, seed, S1_TEST_REQUEST)
    with pytest.raises(PermissionError):
        require_s1_test_request("PRODUCTION", S1_TEST_SEEDS[0], S1_TEST_REQUEST)
    for request in ("PARTIAL_RESULT", "COMPLETE_RESULT", "COMPLETE_PACKAGE", "OUTPUT"):
        with pytest.raises(PermissionError):
            require_s1_test_request(S1_TEST_NAMESPACE, S1_TEST_SEEDS[0], request)


@pytest.mark.parametrize("panel", (0, 1, 2))
def test_complete_counter_population_has_exact_roster_pairing_and_oracle(panel: int) -> None:
    seed = S1_TEST_SEEDS[panel]
    population = native_backend.counter_population(
        seed=seed, panel=panel, batch_index=5, width=768
    )
    for name in ("regimes", "actual_marks", "displayed_marks", "potential_tail"):
        assert np.array_equal(population[name][:256], population[name][256:512])
        assert np.array_equal(population[name][:256], population[name][512:768])
    regimes = population["regimes"][:256]
    if panel == 0:
        assert np.array_equal(np.bincount(regimes[:, 0], minlength=2), np.asarray([128, 128]))
        assert np.array_equal(regimes[:, 0], regimes[:, 1])
        assert np.array_equal(regimes[:, 0], regimes[:, 2])
    elif panel == 1:
        cells = regimes[:, 0] * 2 + regimes[:, 1]
        assert np.array_equal(np.bincount(cells, minlength=4), np.full(4, 64))
        assert np.array_equal(regimes[:, 0], regimes[:, 2])
    else:
        cells = regimes[:, 0] * 2 + regimes[:, 2]
        assert np.array_equal(np.bincount(cells, minlength=4), np.full(4, 64))
        assert np.array_equal(regimes[:, 0], regimes[:, 1])
    if panel != 2:
        assert np.array_equal(population["actual_marks"], population["displayed_marks"])
    for slot in range(8):
        oracle = reference_oracle.run_episode(
            namespace="TEST_ONLY_UCOPE_R01_R03_S0",
            seed=seed,
            panel=panel,
            batch_index=5,
            slot=slot,
            arm=0,
            root_action=0,
            tail_action=0,
        )
        assert np.array_equal(population["regimes"][slot], oracle.regimes)
        assert np.array_equal(population["actual_marks"][slot], oracle.actual_marks)
        assert np.array_equal(population["displayed_marks"][slot], oracle.displayed_marks)
        assert np.array_equal(
            population["potential_tail"][slot],
            reference_oracle.potential_tail_marks(
                seed=seed, panel=panel, batch_index=5, slot=slot
            ),
        )


@pytest.mark.parametrize("panel", (0, 1, 2))
@pytest.mark.parametrize("displayed_count", tuple(range(7)))
def test_all_nonlearned_action_primitives_match_scalar_oracle(
    panel: int, displayed_count: int
) -> None:
    periods = np.asarray(K_TRAIN, dtype=np.int32)
    native = native_backend.nonlearned_actions(
        panel=panel, displayed_count=displayed_count, periods=periods
    )
    oracle = reference_oracle.nonlearned_actions(
        panel=panel, displayed_count=displayed_count
    )
    assert native == oracle
    assert native["forced_probe_blind_dp_root"] == 0
    assert native["immediate_dp_root"] in range(1, 6)


def test_masked_tail_lifecycle_handles_immediate_and_probe_lanes() -> None:
    arms = np.arange(8, dtype=np.int32) % 3
    batch = native_backend.reset_batch(
        seed=S1_TEST_SEEDS[0], panel=0, batch_index=0, arms=arms
    )
    root_actions = np.asarray((0, 1, 0, 2, 0, 3, 0, 4), dtype=np.int32)
    root = batch.root_step(root_actions)
    tail_actions = np.asarray((0, -1, 1, -1, 2, -1, 3, -1), dtype=np.int32)
    tail = batch.tail_step(tail_actions)
    terminal = batch.terminal()
    assert np.array_equal(root["terminal"], root_actions != 0)
    assert np.array_equal(tail[root_actions != 0], np.zeros((4, 3), dtype=np.float32))
    assert np.isfinite(terminal["totals"]).all()
    batch.close()


def test_support_counters_accumulate_exact_schema_and_monotonicity() -> None:
    root = np.tile(np.arange(6, dtype=np.int32), 128)[:768]
    tail = np.where(root == 0, np.arange(768, dtype=np.int32) % 5, -1).astype(np.int32)
    regimes = np.zeros((768, 3), dtype=np.int32)
    displayed = np.zeros((768, 6), dtype=np.int32)
    for lane in range(768):
        slot = lane % 256
        regimes[lane] = (slot // 64 // 2, slot // 64 % 2, slot // 64 // 2)
        displayed[lane, : slot % 7] = 1
    delta = training.support_delta(
        panel=1,
        root_actions=root,
        tail_actions=tail,
        regimes=regimes,
        displayed_marks=displayed,
    )
    counters = training.SupportCounters.empty()
    counters.add_(delta)
    once = counters.sha256()
    counters.add_(delta)
    assert counters.root_actions.sum() == 1536
    assert counters.panel_roster_cells.sum() == 1536
    assert np.array_equal(counters.root_actions, delta.root_actions * 2)
    assert counters.sha256() != once
    assert training.SupportCounters.from_dict(counters.as_dict()).sha256() == counters.sha256()


def test_fixed_fp32_reduction_is_partition_and_order_schedule_independent() -> None:
    values = np.linspace(np.float32(-0.75), np.float32(0.875), 768, dtype=np.float32)
    sequential = training.reduction_frontier(((0, values),))
    partitions = training.reduction_frontier(
        ((512, values[512:]), (0, values[:128]), (128, values[128:512]))
    )
    assert sequential == partitions
    with pytest.raises(ValueError):
        training.reduction_frontier(((0, values[:100]), (101, values[100:])))


def test_exact_fp32_learning_law_steps_once_and_entropy_endpoints() -> None:
    torch.set_num_threads(1)
    bundles = make_paired_bundles(seed=S1_TEST_SEEDS[1], panel=1)
    prepared = training.prepare_training_batch(
        bundles,
        namespace=S1_TEST_NAMESPACE,
        test_seed=S1_TEST_SEEDS[1],
        panel=1,
        batch_index=0,
    )
    support = training.SupportCounters.empty()
    losses = training.apply_training_batch(bundles, support, prepared, batch_number=1)
    assert all(row["entropy_beta"] == pytest.approx(0.01) for row in losses)
    assert {
        int(state["step"].item())
        for bundle in bundles
        for state in bundle.optimizer.state.values()
    } == {1}
    assert all(parameter.dtype == torch.float32 for bundle in bundles for parameter in bundle.parameters())
    terminal_bundle = make_paired_bundles(seed=S1_TEST_SEEDS[2], panel=1)[0]
    terminal_loss = training.frozen_update(
        terminal_bundle, **prepared["data"][0], batch_number=320
    )
    assert terminal_loss["entropy_beta"] == 0.0
    assert not any(
        left.data_ptr() == right.data_ptr()
        for left, right in zip(bundles[0].parameters(), bundles[1].parameters(), strict=True)
    )
    first_seed = native_backend.init_uniforms(
        seed=S1_TEST_SEEDS[0], panel=0, network=0, count=128
    )
    other_seed = native_backend.init_uniforms(
        seed=S1_TEST_SEEDS[1], panel=0, network=0, count=128
    )
    other_panel = native_backend.init_uniforms(
        seed=S1_TEST_SEEDS[0], panel=1, network=0, count=128
    )
    assert not np.array_equal(first_seed, other_seed)
    assert not np.array_equal(first_seed, other_panel)


def test_s1_atomic_frontier_cold_resume_and_90_slot_schema(tmp_path: Path) -> None:
    record = training.run_s1_semantic_core_coupon(
        namespace=S1_TEST_NAMESPACE,
        test_seed=S1_TEST_SEEDS[0],
        test_seed_slot=0,
        panel=0,
        work_root=tmp_path,
    )
    assert record["question_relevant_output"] is False
    assert record["partial_result"] is False
    assert record["complete_r03_package"] is False
    assert record["resume"]["byte_equal"] is True
    assert record["resume"]["support_sha256_equal"] is True
    assert record["resume"]["reduction_frontier_equal"] is True
    assert record["resume"]["optimizer_steps"] == [2]
    assert record["resume"]["committed_step_repeated"] is False
    assert record["manifest"]["slot_count"] == 90
    assert record["manifest"]["complete_r03_package"] is False
    assert record["all_six_arms"]["numeric_values_exposed"] is False


def test_s1_manifest_is_strict_and_cannot_become_a_complete_output() -> None:
    slots = checkpoint.expected_s1_manifest_slots()
    digests = {slot: "a" * 64 for slot in slots}
    manifest = checkpoint.build_s1_structural_manifest(
        digests, namespace=S1_TEST_NAMESPACE, request=S1_TEST_REQUEST
    )
    checkpoint.validate_s1_structural_manifest(manifest)
    with pytest.raises(ValueError):
        checkpoint.build_s1_structural_manifest(
            {key: value for key, value in digests.items() if key != slots[-1]},
            namespace=S1_TEST_NAMESPACE,
            request=S1_TEST_REQUEST,
        )
    with pytest.raises(PermissionError):
        checkpoint.build_s1_structural_manifest(
            digests, namespace=S1_TEST_NAMESPACE, request="COMPLETE_PACKAGE"
        )
    changed = dict(manifest)
    changed["complete_r03_package"] = True
    with pytest.raises(ValueError):
        checkpoint.validate_s1_structural_manifest(changed)
    changed_row = dict(manifest)
    changed_row["slots"] = [dict(row) for row in manifest["slots"]]
    changed_row["slots"][0]["test_seed"] = S1_TEST_SEEDS[1]
    with pytest.raises(ValueError):
        checkpoint.validate_s1_structural_manifest(changed_row)


def test_s1_source_has_no_s2_or_wider_hot_path(tmp_path: Path) -> None:
    package = Path(__file__).resolve().parents[4] / "experiments/candidates/ucope/variable_k_paid_probe_r01_r03"
    for name in ("evaluation.py", "diagnostics.py", "output.py", "production.py"):
        assert not (package / name).exists()
    cpp = (package / "native/ucope_r01_r03_backend.cpp").read_text(encoding="utf-8").lower()
    hot = "\n".join(
        (package / name).read_text(encoding="utf-8").lower()
        for name in ("native_backend.py", "model.py", "training.py")
    )
    for signature in ("double", "long double", "multiprecision"):
        assert signature not in cpp
    for signature in ("torch.float64", "np.float64", "set_default_dtype", "mpmath", "decimal"):
        assert signature not in hot
