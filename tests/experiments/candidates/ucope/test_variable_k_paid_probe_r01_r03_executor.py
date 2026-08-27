from __future__ import annotations

import json
from pathlib import Path

import pytest
import torch

from experiments.candidates.ucope.variable_k_paid_probe_r01_r03 import empirical_transaction
from experiments.candidates.ucope.variable_k_paid_probe_r01_r03.model import make_paired_bundles
from experiments.candidates.ucope.variable_k_paid_probe_r01_r03.production_checkpoint import (
    FrontierIdentity,
    ProductionCheckpointRefusal,
    final_checkpoint_bytes,
    load_frontier_cold,
    save_frontier_atomic,
    write_final_checkpoint_atomic,
)
from experiments.candidates.ucope.variable_k_paid_probe_r01_r03.production_contract import (
    OUTPUT_ROOT,
    checkpoint_slots,
    parameters_document,
)
from experiments.candidates.ucope.variable_k_paid_probe_r01_r03.production_engine import (
    ProductionExecutionRefusal,
    RuntimePaths,
)
from experiments.candidates.ucope.variable_k_paid_probe_r01_r03.production_learner import (
    LearningBoundary,
    ProductionLearningRefusal,
    TECHNICAL_SEEDS,
    prepare_production_batch,
    support_for_arm,
)
from experiments.candidates.ucope.variable_k_paid_probe_r01_r03.production_result import (
    build_value_free_evidence,
)
from experiments.candidates.ucope.variable_k_paid_probe_r01_r03.s2_construction import (
    _cold_load_checkpoint,
)
from experiments.candidates.ucope.variable_k_paid_probe_r01_r03.training import (
    ReductionFrontier,
    SupportCounters,
    apply_training_batch,
)


def _support(panel: int) -> dict[str, object]:
    return {
        "root_visits": [20480, 12288, 12288, 12288, 12288, 12288],
        "tail_visits": [4096] * 5,
        "displayed_count_visits": [2926, 2926, 2926, 2926, 2926, 2926, 2924],
        "balanced_totals": [40960, 40960] if panel == 0 else [20480] * 4,
    }


def test_main_consumes_validated_launch_through_complete_engine(monkeypatch: pytest.MonkeyPatch) -> None:
    launch = {
        "run_id": "ucope-r03-complete-20260827-01",
        "output_root": OUTPUT_ROOT,
        "code_sha": "a" * 40,
        "validated": True,
        "complete_only": True,
        "rerun_permitted": False,
    }
    observed: list[object] = []
    monkeypatch.setattr(empirical_transaction, "validate_launch", lambda *_a, **_k: launch)
    monkeypatch.setattr(
        empirical_transaction,
        "execute_registered_transaction",
        lambda value, *, repository_root: observed.extend((value, repository_root)),
    )
    assert empirical_transaction.main(("technical-placeholder",)) == 0
    assert observed[0] is launch
    assert Path(observed[1]).name == "HMASD-worktrees" or Path(observed[1]).name.startswith("ucope-")


def test_registered_and_technical_learning_boundaries_are_disjoint() -> None:
    registered = LearningBoundary.registered_runtime()
    technical = LearningBoundary.technical_fixture()
    registered.require(101)
    technical.require(TECHNICAL_SEEDS[0])
    with pytest.raises(ProductionLearningRefusal):
        registered.require(TECHNICAL_SEEDS[0])
    with pytest.raises(ProductionLearningRefusal):
        technical.require(101)


def test_nonregistered_batch_is_deterministic_and_advances_one_joint_step() -> None:
    boundary = LearningBoundary.technical_fixture()
    seed = TECHNICAL_SEEDS[0]
    left = make_paired_bundles(seed=seed, panel=0)
    right = make_paired_bundles(seed=seed, panel=0)
    left_support = SupportCounters.empty()
    right_support = SupportCounters.empty()
    prepared_left = prepare_production_batch(
        left, boundary=boundary, master_seed=seed, panel=0, batch_index=0
    )
    prepared_right = prepare_production_batch(
        right, boundary=boundary, master_seed=seed, panel=0, batch_index=0
    )
    assert prepared_left["action_digest"] == prepared_right["action_digest"]
    assert prepared_left["terminal_digest"] == prepared_right["terminal_digest"]
    losses_left = apply_training_batch(left, left_support, prepared_left, batch_number=1)
    losses_right = apply_training_batch(right, right_support, prepared_right, batch_number=1)
    assert losses_left == losses_right
    assert left_support.sha256() == right_support.sha256()
    assert {
        int(state["step"].item())
        for bundle in left
        for state in bundle.optimizer.state.values()
    } == {1}


def test_atomic_frontier_cold_resume_preserves_next_batch_and_state(tmp_path: Path) -> None:
    boundary = LearningBoundary.technical_fixture()
    seed = TECHNICAL_SEEDS[1]
    bundles = make_paired_bundles(seed=seed, panel=1)
    support = SupportCounters.empty()
    prepared = prepare_production_batch(
        bundles, boundary=boundary, master_seed=seed, panel=1, batch_index=0
    )
    apply_training_batch(bundles, support, prepared, batch_number=1)
    reduction = prepared["reduction_frontier"]
    assert isinstance(reduction, ReductionFrontier)
    identity = FrontierIdentity(
        run_id="TEST_ONLY_UCOPE_EXECUTOR",
        code_sha="0" * 40,
        master_seed=seed,
        panel=1,
        namespace=boundary.namespace,
        registered=False,
    )
    path = tmp_path / "frontier.pt"
    save_frontier_atomic(
        path,
        bundles,
        support,
        reduction,
        identity=identity,
        boundary=boundary,
        completed_batch=1,
        counter_frontier=str(prepared["counter_frontier"]),
        native_source_sha256="1" * 64,
        native_artifact_sha256="2" * 64,
    )
    resumed, resumed_support, resumed_reduction, metadata = load_frontier_cold(
        path, identity=identity, boundary=boundary
    )
    assert metadata["completed_batch"] == 1 and metadata["next_batch"] == 2
    assert resumed_support.sha256() == support.sha256()
    assert resumed_reduction == reduction
    for left, right in zip(bundles, resumed, strict=True):
        for name, tensor in left.scorer.state_dict().items():
            assert torch.equal(tensor, right.scorer.state_dict()[name])
        for name, tensor in left.baseline.state_dict().items():
            assert torch.equal(tensor, right.baseline.state_dict()[name])


def test_final_checkpoint_is_create_only_and_s2_compatible(tmp_path: Path) -> None:
    boundary = LearningBoundary.technical_fixture()
    seed = TECHNICAL_SEEDS[2]
    bundle = make_paired_bundles(seed=seed, panel=0)[0]
    payload = final_checkpoint_bytes(
        bundle,
        arm=0,
        panel=0,
        master_seed=seed,
        support=_support(0),
        boundary=boundary,
    )
    decoded = json.loads(payload)
    assert decoded["batch"] == 320
    assert decoded["model_sha256"]
    assert decoded["support"] == _support(0)
    assert "result" not in decoded and "value" not in decoded
    path = tmp_path / "slot.json"
    write_final_checkpoint_atomic(path, payload)
    loaded = _cold_load_checkpoint(path, tmp_path)
    assert (loaded.arm, loaded.panel, loaded.master_seed, loaded.batch) == (0, 0, seed, 320)
    with pytest.raises(ProductionCheckpointRefusal, match="create-only"):
        write_final_checkpoint_atomic(path, payload)


def test_value_free_terminal_evidence_contains_hashes_not_values() -> None:
    evidence = build_value_free_evidence(
        run_id="ucope-r03-complete-20260827-01",
        code_sha="a" * 40,
        checkpoint_manifest_sha256="b" * 64,
        completion={
            "schema": "UCOPE_R01_R03_S2_COMPLETION_MANIFEST_V1",
            "completeness_digest": "c" * 64,
            "package_sha256": "d" * 64,
        },
        sealed_result_sha256="e" * 64,
    )
    assert evidence["complete_r03_package"] is True
    assert evidence["partial_result"] is False
    assert evidence["scientific_values_in_evidence"] is False
    assert not ({"estimand", "effect", "intervals", "attribution"} & set(evidence))


def test_runtime_roster_and_fresh_output_gate_are_exact(tmp_path: Path) -> None:
    assert len(checkpoint_slots()) == parameters_document()["checkpoint_slot_count"] == 90
    root = tmp_path
    output = root / Path(*OUTPUT_ROOT.split("/"))
    for name in ("checkpoints", "artifacts", "metrics"):
        (output / name).mkdir(parents=True, exist_ok=True)
    (output / "manifest.json").write_text("{}", encoding="utf-8")
    paths = RuntimePaths.from_repository(root)
    paths.require_fresh_prepared_outputs()
    (paths.metrics / "residue").write_text("technical", encoding="utf-8")
    with pytest.raises(ProductionExecutionRefusal, match="not empty"):
        paths.require_fresh_prepared_outputs()
