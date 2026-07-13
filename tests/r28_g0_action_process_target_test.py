from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pytest

import scripts.analyze_r28_g0_action_process_target as cli
from ha_ctse_process import r28_g0_target as target


def make_score(name: str, accuracy: float = 0.5) -> target.HeadScore:
    interval = target.BootstrapInterval(
        estimate=accuracy,
        lower=0.30,
        upper=0.70,
        reps=10,
        seed=target.BOOTSTRAP_SEED,
    )
    return target.HeadScore(
        name=name,
        train_accuracy=accuracy,
        validation_accuracy=accuracy,
        test_accuracy=accuracy,
        test_macro_f1=accuracy,
        duration_test_accuracy={duration: accuracy for duration in target.DURATION_STEPS},
        accuracy_interval=interval,
        train_minus_test=0.0,
        optimizer_steps=5,
        validation_evaluations=1,
        temperature=1.0,
        log_prob_true=np.zeros(4, dtype=np.float32),
        predictions=np.zeros(4, dtype=np.int64),
    )


def make_result(checkpoint_id: str, status: str) -> target.CheckpointResult:
    return target.CheckpointResult(
        checkpoint_id=checkpoint_id,
        status=status,  # type: ignore[arg-type]
        classification="PASS_TARGET_NULLS" if status == "PASS" else status,
        reasons=(),
        support={"valid_resets": 64},
        q_full=make_score("q_full"),
        q_context=make_score("q_context"),
        q_pre=make_score("q_pre"),
        q_full_artifact=None,
        q_context_artifact=None,
        q_pre_artifact=None,
        metrics={},
        support_envelope=None,
    )


def test_family_requires_final_plus_one_earlier_pass():
    status, classification = target.classify_family(
        [
            make_result("arm0_update25", "PASS"),
            make_result("arm0_update30", "FAIL"),
            make_result("arm0_final", "PASS"),
        ]
    )
    assert (status, classification) == ("PASS", "PASS_TARGET_NULLS")

    status, classification = target.classify_family(
        [
            make_result("arm0_update25", "PASS"),
            make_result("arm0_update30", "PASS"),
            make_result("arm0_final", "FAIL"),
        ]
    )
    assert (status, classification) == ("MIXED", "MIXED_TARGET")


def test_support_reasons_encode_registered_reset_and_prefix_floors():
    support = {
        "valid_resets": 47,
        "prefix_counts": [16, 16, 15],
        "split_counts": {"train": 31, "validation": 9, "test": 9},
        "split_prefix_counts": {
            "train": [10, 10, 11],
            "validation": [3, 3, 3],
            "test": [3, 3, 3],
        },
        "pulse_pairs": 1,
    }
    reasons = target.support_reasons(support)
    assert any("valid resets" in item for item in reasons)
    assert any("split counts" in item for item in reasons)


def test_validate_result_requires_pass_scorer_only(tmp_path: Path):
    report = {
        "experiment_id": target.EXPERIMENT_ID,
        "status": "FAIL",
        "classification": "FAIL_TARGET",
        "device": "cuda",
        "scientific_contract": target.SCIENTIFIC_CONTRACT,
        "checkpoints": [
            {"checkpoint_id": checkpoint_id} for checkpoint_id in target.CHECKPOINT_IDS
        ],
        "scorer": None,
    }
    json_path = tmp_path / "r28_g0_action_process_target.json"
    md_path = tmp_path / "r28_g0_action_process_target.md"
    json_path.write_text(
        json.dumps(target.jsonable(report), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    md_path.write_text(cli._markdown(report), encoding="utf-8")

    result = cli.run_validate_result(argparse.Namespace(output_dir=str(tmp_path)))
    assert result["scientific_status"] == "FAIL"
    assert result["classification"] == "FAIL_TARGET"

    report["status"] = "PASS"
    report["classification"] = "PASS_TARGET_NULLS"
    json_path.write_text(
        json.dumps(target.jsonable(report), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    md_path.write_text(cli._markdown(report), encoding="utf-8")
    with pytest.raises(target.EvidenceError, match="missing final scorer"):
        cli.run_validate_result(argparse.Namespace(output_dir=str(tmp_path)))


def test_runner_dry_run_contract_is_static_and_hash_free():
    text = Path("scripts/run_r28_g0_action_process_target_cloud.sh").read_text(
        encoding="utf-8"
    )
    assert "--dry-run" in text
    assert "R27_RUN_ROOT" in text
    assert "validate-result" in text
    assert "CPU fallback is forbidden" in text
    assert "checksum" not in text.lower()
    assert "sha256" not in text.lower()
    assert "sha1" not in text.lower()
    assert "hash" not in text.lower()
