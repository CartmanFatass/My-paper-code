from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

import numpy as np
import pytest
import torch

from experiments.candidates.ucope.variable_k_paid_probe_r01_r03 import (
    benchmark,
    checkpoint,
    native_backend,
    model,
    reference_oracle,
    training,
)
from experiments.candidates.ucope.variable_k_paid_probe_r01_r03.contract import (
    COUNTER_LAYOUT_ID,
    K_TRAIN,
    REGISTERED_MASTER_SEEDS,
    S1_TEST_NAMESPACE,
    S1_TEST_REQUEST,
    S1_TEST_SEEDS,
    TEST_NAMESPACE,
    TRAINING_BATCHES,
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


def test_s1_scalar_oracle_bridge_is_explicit_and_fail_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    mechanism = reference_oracle._run_episode
    mechanism_calls: list[dict[str, object]] = []

    def observed_mechanism(**kwargs: object) -> reference_oracle.OracleEpisode:
        mechanism_calls.append(dict(kwargs))
        return mechanism(**kwargs)

    monkeypatch.setattr(reference_oracle, "_run_episode", observed_mechanism)
    assert reference_oracle.S1_SCALAR_ORACLE_BRIDGE_ID == (
        "UCOPE_R01_R03_S1_TEST_TO_RETAINED_S0_SCALAR_MECHANISM_V1"
    )
    coordinate = {
        "seed": S1_TEST_SEEDS[0],
        "panel": 0,
        "batch_index": 5,
        "slot": 3,
        "arm": 2,
        "root_action": 0,
        "tail_action": 4,
    }
    bridged = reference_oracle.run_s1_test_episode(
        namespace=S1_TEST_NAMESPACE,
        request=S1_TEST_REQUEST,
        **coordinate,
    )
    retained = reference_oracle.run_episode(
        namespace=TEST_NAMESPACE,
        **coordinate,
    )
    for name in (
        "regimes",
        "root_features",
        "root_baseline",
        "actual_marks",
        "displayed_marks",
        "probe_components",
        "tail_features",
        "tail_baseline",
        "components",
    ):
        assert np.array_equal(getattr(bridged, name), getattr(retained, name))
    assert bridged.total.view(np.uint32) == retained.total.view(np.uint32)
    with pytest.raises(PermissionError):
        reference_oracle.run_s1_test_episode(
            namespace=TEST_NAMESPACE,
            request=S1_TEST_REQUEST,
            **coordinate,
        )
    with pytest.raises(PermissionError):
        reference_oracle.run_s1_test_episode(
            namespace=S1_TEST_NAMESPACE,
            request="COMPLETE_RESULT",
            **coordinate,
        )
    with pytest.raises(PermissionError):
        reference_oracle.run_s1_test_episode(
            namespace=S1_TEST_NAMESPACE,
            request=S1_TEST_REQUEST,
            **(coordinate | {"seed": min(REGISTERED_MASTER_SEEDS)}),
        )
    assert len(mechanism_calls) == 2


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
        oracle = reference_oracle.run_s1_test_episode(
            namespace=S1_TEST_NAMESPACE,
            request=S1_TEST_REQUEST,
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


def test_all_six_arm_digest_executes_each_fixture_path(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    learned_calls: list[tuple[int, int, int]] = []
    nonlearned_calls: list[tuple[int, int]] = []
    reset_batch = native_backend.reset_batch
    nonlearned_actions = native_backend.nonlearned_actions
    sample_actions = native_backend.sample_actions
    scorer_forward = model.ActionScorer.forward
    root_step = native_backend.NativeBatch.root_step
    tail_step = native_backend.NativeBatch.tail_step
    terminal = native_backend.NativeBatch.terminal
    close = native_backend.NativeBatch.close
    scorer_shapes: list[tuple[int, ...]] = []
    sample_calls: list[tuple[int, int]] = []
    lifecycle_calls: list[tuple[int, str]] = []

    def observed_reset_batch(*args: object, **kwargs: object) -> object:
        arms = np.asarray(kwargs["arms"])
        assert arms.shape == (8,)
        assert np.unique(arms).size == 1
        learned_calls.append(
            (int(kwargs["seed"]), int(kwargs["panel"]), int(arms[0]))
        )
        return reset_batch(*args, **kwargs)

    def observed_scorer_forward(
        scorer: model.ActionScorer, features: torch.Tensor,
    ) -> torch.Tensor:
        scorer_shapes.append(tuple(features.shape))
        return scorer_forward(scorer, features)

    def observed_sample_actions(*args: object, **kwargs: object) -> np.ndarray:
        arms = np.asarray(kwargs["arms"])
        assert arms.shape == (8,)
        assert np.unique(arms).size == 1
        sample_calls.append((int(arms[0]), int(kwargs["decision_code"])))
        return sample_actions(*args, **kwargs)

    def observed_root_step(
        batch: native_backend.NativeBatch, actions: np.ndarray,
    ) -> dict[str, np.ndarray]:
        lifecycle_calls.append((int(batch.arms[0]), "root"))
        return root_step(batch, actions)

    def observed_tail_step(
        batch: native_backend.NativeBatch, actions: np.ndarray,
    ) -> np.ndarray:
        lifecycle_calls.append((int(batch.arms[0]), "tail"))
        return tail_step(batch, actions)

    def observed_terminal(
        batch: native_backend.NativeBatch,
    ) -> dict[str, np.ndarray]:
        lifecycle_calls.append((int(batch.arms[0]), "terminal"))
        return terminal(batch)

    def observed_close(batch: native_backend.NativeBatch) -> None:
        lifecycle_calls.append((int(batch.arms[0]), "close"))
        close(batch)

    def observed_nonlearned_actions(*args: object, **kwargs: object) -> object:
        nonlearned_calls.append(
            (int(kwargs["panel"]), int(kwargs["displayed_count"]))
        )
        return nonlearned_actions(*args, **kwargs)

    monkeypatch.setattr(native_backend, "reset_batch", observed_reset_batch)
    monkeypatch.setattr(
        native_backend, "nonlearned_actions", observed_nonlearned_actions,
    )
    monkeypatch.setattr(model.ActionScorer, "forward", observed_scorer_forward)
    monkeypatch.setattr(
        native_backend, "sample_actions", observed_sample_actions,
    )
    monkeypatch.setattr(
        native_backend.NativeBatch, "root_step", observed_root_step,
    )
    monkeypatch.setattr(
        native_backend.NativeBatch, "tail_step", observed_tail_step,
    )
    monkeypatch.setattr(
        native_backend.NativeBatch, "terminal", observed_terminal,
    )
    monkeypatch.setattr(native_backend.NativeBatch, "close", observed_close)
    record = training.all_six_arm_semantic_digest()
    assert learned_calls == [
        (S1_TEST_SEEDS[arm], arm, arm) for arm in range(3)
    ]
    assert scorer_shapes == [
        shape
        for _ in range(3)
        for shape in ((8, 6, 13), (8, 5, 13))
    ]
    assert sample_calls == [
        (arm, decision)
        for arm in range(3)
        for decision in (0, 1)
    ]
    assert lifecycle_calls == [
        (arm, stage)
        for arm in range(3)
        for stage in ("root", "tail", "terminal", "close")
    ]
    assert nonlearned_calls == [
        (panel, displayed_count)
        for panel in range(3)
        for displayed_count in range(7)
    ]
    assert set(record) == {
        "learned_arms",
        "nonlearned_arms",
        "learned_fixture_calls",
        "nonlearned_fixture_calls",
        "learned_action_sha256",
        "nonlearned_action_sha256",
        "numeric_values_exposed",
        "question_relevant_output",
    }
    assert record["learned_arms"] == (
        "COUNT_FP32", "RAW_FP32", "BELIEF_FEATURE_FP32",
    )
    assert record["nonlearned_arms"] == (
        "BELIEF_DP", "IMMEDIATE_DP", "FORCED_PROBE_BLIND_DP",
    )
    assert record["learned_fixture_calls"] == 3
    assert record["nonlearned_fixture_calls"] == 21
    for name in ("learned_action_sha256", "nonlearned_action_sha256"):
        digest = record[name]
        assert isinstance(digest, str)
        assert len(digest) == 64
        assert set(digest) <= set("0123456789abcdef")
    assert record["numeric_values_exposed"] is False
    assert record["question_relevant_output"] is False


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


def test_all_s1_frontier_sha_fields_require_exact_lowercase_hex() -> None:
    reduction = training.reduction_frontier(
        ((0, np.arange(8, dtype=np.float32)),)
    )
    metadata: dict[str, object] = {
        "test_seed": S1_TEST_SEEDS[0],
        "test_seed_slot": 0,
        "panel": 0,
        "completed_batch": 1,
        "next_batch": 2,
        "counter_frontier": "a" * 64,
        "reduction_frontier": reduction.as_dict(),
        "batch_width": 768,
        "worker_count": 1,
        "torch_threads": 1,
        "source_sha256": "b" * 64,
        "native_artifact_sha256": "c" * 64,
        "counter_layout_id": COUNTER_LAYOUT_ID,
    }
    checkpoint._validate_s1_metadata(metadata)
    invalid_values: tuple[object, ...] = (
        None,
        "a" * 63,
        "A" * 64,
        "g" * 64,
    )
    for field in (
        "counter_frontier",
        "source_sha256",
        "native_artifact_sha256",
        "ordered_values_sha256",
    ):
        for invalid in invalid_values:
            changed = dict(metadata)
            if field == "ordered_values_sha256":
                changed_reduction = dict(reduction.as_dict())
                changed_reduction[field] = invalid
                changed["reduction_frontier"] = changed_reduction
            else:
                changed[field] = invalid
            with pytest.raises(ValueError):
                checkpoint._validate_s1_metadata(changed)


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


def test_s1_atomic_resume_and_real_90_slot_checkpoint_shape(
    tmp_path: Path,
) -> None:
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
    assert record["resume"]["counter_frontier_equal"] is True
    learning = record["learning_observations"]
    assert set(learning) == {
        "first_entropy_betas",
        "second_entropy_betas",
        "parameter_dtypes",
        "optimizer_state_dtypes",
        "observed_optimizer_steps",
    }
    assert learning["first_entropy_betas"] == pytest.approx([0.01] * 3)
    expected_second_beta = 0.01 * 318 / 319
    assert learning["second_entropy_betas"]["uninterrupted"] == pytest.approx(
        [expected_second_beta] * 3
    )
    assert learning["second_entropy_betas"]["cold_resumed"] == pytest.approx(
        [expected_second_beta] * 3
    )
    assert learning["parameter_dtypes"] == {
        "uninterrupted": ["torch.float32"],
        "cold_resumed": ["torch.float32"],
    }
    assert learning["optimizer_state_dtypes"] == {
        "uninterrupted": ["torch.float32"],
        "cold_resumed": ["torch.float32"],
    }
    assert learning["observed_optimizer_steps"] == {
        "after_first_update": [1],
        "after_cold_load": [1],
        "after_second_uninterrupted_update": [2],
        "after_second_resumed_update": [2],
    }
    support = record["support"]
    assert support["round_trip_equal"] is True
    assert support["first_to_second_monotone"] is True
    assert support["first_to_second_progressed"] is True
    assert support["first_sha256"] != support["second_sha256"]
    assert support["second_sha256"] == support["sha256"]
    assert "schema_valid" not in support
    assert "monotone" not in support
    assert "fp32_hot_path" not in record
    assert "fixed_fp32_tree" not in record["reduction"]
    summary = record["manifest"]
    assert set(summary) == {
        "schema",
        "slot_count",
        "complete_r03_package",
        "sha256",
        "persisted_slot_count",
        "all_slot_files_present",
        "all_slot_digests_verified",
    }
    assert summary["schema"] == checkpoint.S1_MANIFEST_SCHEMA
    assert summary["slot_count"] == 90
    assert summary["persisted_slot_count"] == 90
    assert summary["all_slot_files_present"] is True
    assert summary["all_slot_digests_verified"] is True
    assert summary["complete_r03_package"] is False
    artifact_root, manifest_path = checkpoint.s1_test_checkpoint_paths(tmp_path)
    assert manifest_path.is_file()
    assert hashlib.sha256(manifest_path.read_bytes()).hexdigest() == summary["sha256"]
    manifest = checkpoint.load_s1_manifest_cold(
        manifest_path,
        artifact_root=artifact_root,
        expected_sha256=summary["sha256"],
    )
    assert manifest["checkpoint_shape_schema"] == (
        checkpoint.S1_CHECKPOINT_SHAPE_SCHEMA
    )
    assert manifest["checkpoint_shape_training_batches"] == TRAINING_BATCHES
    assert manifest["fixture_completed_training_batches"] == 0
    assert manifest["registered_training_executed"] is False
    assert manifest["registered_evaluation_executed"] is False
    assert manifest["scientific_final_checkpoint"] is False
    assert manifest["promotable"] is False
    assert manifest["question_relevant_output"] is False
    assert manifest["partial_result"] is False
    assert manifest["complete_r03_package"] is False
    assert "synthetic" not in json.dumps(manifest, sort_keys=True).lower()
    files = sorted(path for path in artifact_root.rglob("*") if path.is_file())
    assert len(files) == 90
    rows = manifest["slots"]
    assert len(rows) == 90
    assert {
        (row["test_seed_slot"], row["panel"], row["learned_arm"])
        for row in rows
    } == {
        (seed_slot, panel, learned_arm)
        for seed_slot in range(10)
        for panel in range(3)
        for learned_arm in range(3)
    }
    artifact_digests: set[str] = set()
    state_digests: set[str] = set()
    for row in rows:
        assert row["namespace"] == S1_TEST_NAMESPACE
        assert row["request"] == S1_TEST_REQUEST
        assert row["checkpoint_shape_schema"] == (
            checkpoint.S1_CHECKPOINT_SHAPE_SCHEMA
        )
        assert row["checkpoint_shape_training_batches"] == TRAINING_BATCHES
        assert row["fixture_completed_training_batches"] == 0
        assert row["registered_training_executed"] is False
        assert row["registered_evaluation_executed"] is False
        assert row["dtype"] == "torch.float32"
        assert row["question_relevant_output"] is False
        assert row["partial_result"] is False
        assert row["complete_r03_package"] is False
        assert row["scientific_final_checkpoint"] is False
        assert row["promotable"] is False
        for name in ("state_sha256", "artifact_sha256"):
            digest = row[name]
            assert isinstance(digest, str)
            assert len(digest) == 64
            assert set(digest) <= set("0123456789abcdef")
        artifact = artifact_root / row["relative_path"]
        assert artifact.is_file()
        assert artifact.stat().st_size == row["artifact_bytes"]
        assert hashlib.sha256(artifact.read_bytes()).hexdigest() == row[
            "artifact_sha256"
        ]
        loaded_state_sha256, loaded_state_bytes = checkpoint.load_s1_test_slot_cold(
            artifact,
            namespace=S1_TEST_NAMESPACE,
            request=S1_TEST_REQUEST,
            panel=row["panel"],
            test_seed_slot=row["test_seed_slot"],
            learned_arm=row["learned_arm"],
            expected_artifact_sha256=row["artifact_sha256"],
            expected_artifact_bytes=row["artifact_bytes"],
        )
        assert loaded_state_sha256 == row["state_sha256"]
        assert loaded_state_bytes == row["state_bytes"]
        artifact_digests.add(row["artifact_sha256"])
        state_digests.add(row["state_sha256"])
    assert len(artifact_digests) == 90
    assert len(state_digests) == 30
    assert record["all_six_arms"]["learned_fixture_calls"] == 3
    assert record["all_six_arms"]["nonlearned_fixture_calls"] == 21
    assert record["all_six_arms"]["numeric_values_exposed"] is False
    assert record["all_six_arms"]["question_relevant_output"] is False

    slot_artifacts = {row["slot"]: row for row in rows}
    with pytest.raises(ValueError):
        checkpoint.build_s1_structural_manifest(
            {
                slot: row
                for slot, row in slot_artifacts.items()
                if slot != checkpoint.expected_s1_manifest_slots()[-1]
            },
            artifact_root=artifact_root,
            namespace=S1_TEST_NAMESPACE,
            request=S1_TEST_REQUEST,
        )
    with pytest.raises(PermissionError):
        checkpoint.build_s1_structural_manifest(
            slot_artifacts,
            artifact_root=artifact_root,
            namespace=S1_TEST_NAMESPACE,
            request="COMPLETE_PACKAGE",
        )
    changed = dict(manifest)
    changed["complete_r03_package"] = True
    with pytest.raises(ValueError):
        checkpoint.validate_s1_structural_manifest(
            changed, artifact_root=artifact_root,
        )
    changed_row = dict(manifest)
    changed_row["slots"] = [dict(row) for row in rows]
    changed_row["slots"][0]["test_seed"] = S1_TEST_SEEDS[1]
    with pytest.raises(ValueError):
        checkpoint.validate_s1_structural_manifest(
            changed_row, artifact_root=artifact_root,
        )
    for field in ("state_sha256", "artifact_sha256"):
        for invalid in ("A" * 64, "g" * 64, "a" * 63):
            changed_digest = dict(manifest)
            changed_digest["slots"] = [dict(row) for row in rows]
            changed_digest["slots"][0][field] = invalid
            with pytest.raises(ValueError):
                checkpoint.validate_s1_structural_manifest(
                    changed_digest, artifact_root=artifact_root,
                )
    for invalid_manifest_sha in ("A" * 64, "g" * 64, "a" * 63):
        with pytest.raises(ValueError):
            checkpoint.load_s1_manifest_cold(
                manifest_path,
                artifact_root=artifact_root,
                expected_sha256=invalid_manifest_sha,
            )
    with files[0].open("rb") as stream:
        slot_payload = torch.load(stream, map_location="cpu", weights_only=False)
    for invalid_state_sha in ("A" * 64, "g" * 64, "a" * 63):
        changed_payload = dict(slot_payload)
        changed_payload["state_sha256"] = invalid_state_sha
        with pytest.raises(ValueError):
            checkpoint._validate_s1_slot_payload(
                changed_payload,
                namespace=S1_TEST_NAMESPACE,
                request=S1_TEST_REQUEST,
                panel=rows[0]["panel"],
                test_seed_slot=rows[0]["test_seed_slot"],
                learned_arm=rows[0]["learned_arm"],
            )
    missing_file = files[-1]
    missing_bytes = missing_file.read_bytes()
    missing_file.unlink()
    with pytest.raises(ValueError):
        checkpoint.validate_s1_structural_manifest(
            manifest, artifact_root=artifact_root,
        )
    missing_file.write_bytes(missing_bytes)
    corrupt_file = files[0]
    corrupted_bytes = bytearray(corrupt_file.read_bytes())
    corrupted_bytes[-1] ^= 1
    corrupt_file.write_bytes(corrupted_bytes)
    with pytest.raises(ValueError):
        checkpoint.validate_s1_structural_manifest(
            manifest, artifact_root=artifact_root,
        )


def test_s1_benchmark_oracle_helper_uses_explicit_bridge(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    bridge = reference_oracle.run_s1_test_episode
    bridge_calls: list[dict[str, object]] = []

    def observed_bridge(
        **kwargs: object,
    ) -> reference_oracle.OracleEpisode:
        bridge_calls.append(dict(kwargs))
        return bridge(**kwargs)

    def forbidden_s0_oracle(**kwargs: object) -> reference_oracle.OracleEpisode:
        pytest.fail(f"S1 benchmark used retained S0 entrypoint directly: {kwargs}")

    monkeypatch.setattr(
        reference_oracle, "run_s1_test_episode", observed_bridge,
    )
    monkeypatch.setattr(reference_oracle, "run_episode", forbidden_s0_oracle)
    digest = benchmark._s1_oracle_lifecycle(width=3, repeats=2)
    assert len(digest) == 64
    assert set(digest) <= set("0123456789abcdef")
    assert len(bridge_calls) == 6
    assert all(
        call["namespace"] == S1_TEST_NAMESPACE
        and call["request"] == S1_TEST_REQUEST
        and call["seed"] in S1_TEST_SEEDS
        for call in bridge_calls
    )
    assert reference_oracle.S1_SCALAR_ORACLE_BRIDGE_ID == (
        "UCOPE_R01_R03_S1_TEST_TO_RETAINED_S0_SCALAR_MECHANISM_V1"
    )


def test_observed_learning_and_support_gate_evidence_fail_closed() -> None:
    second_beta = 0.01 * 318 / 319
    learning: dict[str, object] = {
        "first_entropy_betas": [0.01] * 3,
        "second_entropy_betas": {
            "uninterrupted": [second_beta] * 3,
            "cold_resumed": [second_beta] * 3,
        },
        "parameter_dtypes": {
            "uninterrupted": ["torch.float32"],
            "cold_resumed": ["torch.float32"],
        },
        "optimizer_state_dtypes": {
            "uninterrupted": ["torch.float32"],
            "cold_resumed": ["torch.float32"],
        },
        "observed_optimizer_steps": {
            "after_first_update": [1],
            "after_cold_load": [1],
            "after_second_uninterrupted_update": [2],
            "after_second_resumed_update": [2],
        },
    }
    assert benchmark._observed_fp32_learning_evidence(learning) is True
    invalid_learning: list[dict[str, object]] = []
    changed = json.loads(json.dumps(learning))
    changed["first_entropy_betas"][0] = 0.02
    invalid_learning.append(changed)
    changed = json.loads(json.dumps(learning))
    changed["second_entropy_betas"]["uninterrupted"][1] = 0.02
    invalid_learning.append(changed)
    changed = json.loads(json.dumps(learning))
    changed["second_entropy_betas"]["cold_resumed"][1] = 0.02
    invalid_learning.append(changed)
    changed = json.loads(json.dumps(learning))
    changed["parameter_dtypes"]["cold_resumed"] = ["torch.float64"]
    invalid_learning.append(changed)
    changed = json.loads(json.dumps(learning))
    changed["optimizer_state_dtypes"]["uninterrupted"] = ["torch.float64"]
    invalid_learning.append(changed)
    for name in (
        "after_first_update",
        "after_cold_load",
        "after_second_uninterrupted_update",
        "after_second_resumed_update",
    ):
        changed = json.loads(json.dumps(learning))
        changed["observed_optimizer_steps"][name] = [99]
        invalid_learning.append(changed)
    assert all(
        benchmark._observed_fp32_learning_evidence(value) is False
        for value in invalid_learning
    )
    assert benchmark._observed_fp32_learning_evidence(None) is False

    support: dict[str, object] = {
        "first_sha256": "a" * 64,
        "second_sha256": "b" * 64,
        "round_trip_equal": True,
        "first_to_second_monotone": True,
        "first_to_second_progressed": True,
        "root_total": 1536,
        "tail_total": 256,
        "roster_total": 1536,
        "displayed_count_total": 256,
        "sha256": "b" * 64,
    }
    assert benchmark._observed_support_evidence(support) is True
    invalid_support: list[dict[str, object]] = []
    for name in (
        "round_trip_equal",
        "first_to_second_monotone",
        "first_to_second_progressed",
    ):
        changed = dict(support)
        changed[name] = False
        invalid_support.append(changed)
    changed = dict(support)
    changed["second_sha256"] = "c" * 64
    invalid_support.append(changed)
    changed = dict(support)
    changed["first_sha256"] = "A" * 64
    invalid_support.append(changed)
    assert all(
        benchmark._observed_support_evidence(value) is False
        for value in invalid_support
    )
    assert benchmark._observed_support_evidence(None) is False


def test_benchmark_main_dispatches_s1_and_reports_selected_schema(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    work_root = tmp_path / "benchmark-work"
    output = tmp_path / "benchmark-record.json"
    observed: dict[str, Path] = {}

    def fake_s1_runner(path: Path) -> dict[str, object]:
        observed["work_root"] = path
        return {
            "schema": "UCOPE_R01_R03_S1_RESULT_BLIND_BENCHMARK_V1",
            "all_s1_gates_pass": True,
            "measured_resources": {"durable_bytes": 0},
            "complete_plan_projection": {
                "projection_only": True,
                "executed_test_worker_count": 8,
                "projection_core_ceiling": 24,
            },
        }

    def forbidden_s0_runner(path: Path) -> dict[str, object]:
        pytest.fail(f"S1 CLI dispatched the S0 runner for {path}")

    monkeypatch.setattr(benchmark, "_benchmark_s1", fake_s1_runner)
    monkeypatch.setattr(benchmark, "_benchmark", forbidden_s0_runner)
    monkeypatch.setattr(sys, "argv", ["ucope-benchmark-program", "--stage", "s0"])
    argv = [
        "--stage",
        "s1",
        "--work-root",
        str(work_root),
        "--output",
        str(output),
    ]
    assert benchmark.main(argv) == 0
    assert observed == {"work_root": work_root.resolve()}
    persisted = json.loads(output.read_text(encoding="utf-8"))
    assert persisted["schema"] == "UCOPE_R01_R03_S1_RESULT_BLIND_BENCHMARK_V1"
    assert persisted["stage"] == "s1"
    assert persisted["command"]["stage"] == "s1"
    assert persisted["command"]["argv"] == ["ucope-benchmark-program", *argv]
    summary = json.loads(capsys.readouterr().out)
    assert summary["stage"] == "s1"
    assert summary["schema"] == "UCOPE_R01_R03_S1_RESULT_BLIND_BENCHMARK_V1"
    assert summary["command"]["argv"] == ["ucope-benchmark-program", *argv]
    assert summary["all_s1_gates_pass"] is True


def test_benchmark_source_drift_refuses_before_evidence_write(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    output = tmp_path / "drifted-record.json"
    source_path = (
        "experiments/candidates/ucope/variable_k_paid_probe_r01_r03/"
        "training.py"
    )

    def drifted_runner(path: Path) -> dict[str, object]:
        return {
            "schema": "UCOPE_R01_R03_S1_RESULT_BLIND_BENCHMARK_V1",
            "all_s1_gates_pass": True,
            "measured_resources": {"durable_bytes": 0},
            "complete_plan_projection": {"projection_only": True},
            "current_source_sha256": {source_path: "a" * 64},
        }

    monkeypatch.setattr(benchmark, "_benchmark_s1", drifted_runner)
    monkeypatch.setattr(
        benchmark, "_sha256_path", lambda path: "b" * 64,
    )
    monkeypatch.setattr(sys, "argv", ["ucope-benchmark-program"])
    with pytest.raises(
        RuntimeError,
        match="UCOPE benchmark source map changed during execution",
    ):
        benchmark.main(
            [
                "--stage", "s1",
                "--work-root", str(tmp_path / "drift-work"),
                "--output", str(output),
            ]
        )
    assert not output.exists()


def test_benchmark_paths_reject_symlinks_without_external_writes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    outside_file = tmp_path / "outside.json"
    outside_file.write_text("sentinel", encoding="utf-8")
    outside_directory = tmp_path / "outside-directory"
    outside_directory.mkdir()
    work_link = tmp_path / "linked-work"
    output_link = tmp_path / "linked-output.json"
    output_parent_link = tmp_path / "linked-output-parent"
    try:
        work_link.symlink_to(outside_directory, target_is_directory=True)
        output_link.symlink_to(outside_file)
        output_parent_link.symlink_to(
            outside_directory, target_is_directory=True,
        )
    except OSError as error:
        pytest.skip(f"symlink creation is unavailable: {error}")
    runner_called = False

    def forbidden_runner(path: Path) -> dict[str, object]:
        nonlocal runner_called
        runner_called = True
        pytest.fail(f"benchmark runner reached after path refusal for {path}")

    monkeypatch.setattr(benchmark, "_benchmark_s1", forbidden_runner)
    monkeypatch.setattr(sys, "argv", ["ucope-benchmark-program"])
    with pytest.raises(
        ValueError, match="work root path must not contain symlink components",
    ):
        benchmark.main(
            [
                "--stage", "s1",
                "--work-root", str(work_link),
                "--output", str(tmp_path / "unused.json"),
            ]
        )
    with pytest.raises(
        ValueError, match="output path must not contain symlink components",
    ):
        benchmark.main(
            [
                "--stage", "s1",
                "--work-root", str(tmp_path / "ordinary-work"),
                "--output", str(output_link),
            ]
        )
    with pytest.raises(
        ValueError, match="output path must not contain symlink components",
    ):
        benchmark.main(
            [
                "--stage", "s1",
                "--work-root", str(tmp_path / "ordinary-work"),
                "--output", str(output_parent_link / "record.json"),
            ]
        )
    with pytest.raises(
        ValueError, match="work root path must be canonical",
    ):
        benchmark.main(
            [
                "--stage", "s1",
                "--work-root",
                str(tmp_path / "lexical-parent" / ".." / "work"),
                "--output", str(tmp_path / "unused.json"),
            ]
        )
    assert runner_called is False
    assert outside_file.read_text(encoding="utf-8") == "sentinel"
    assert not (outside_directory / "record.json").exists()


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
