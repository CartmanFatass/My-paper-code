from __future__ import annotations

import json

import pytest

from experiments.candidates.capability_bound_semantic_currentness_learnability_r01.artifact import (
    _atomic_create_only_bytes,
    publish_complete_result,
    validate_complete_result,
    to_jsonable,
)
from experiments.candidates.capability_bound_semantic_currentness_learnability_r01.analysis import reduce_finite_panel
from experiments.candidates.capability_bound_semantic_currentness_learnability_r01.contract import describe
from experiments.candidates.capability_bound_semantic_currentness_learnability_r01.cli import main


def test_describe_is_result_blind_and_reports_ready_contract(capsys) -> None:
    assert main(["describe"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["result_activity"] == "ZERO"
    assert payload["result_fields"] == []
    assert payload["ready_for_production"] is True
    assert payload["production_blocker"] is None


def test_run_has_only_manifest_and_routes_sole_runner_without_production(monkeypatch, tmp_path, capsys) -> None:
    target = tmp_path / "result.json"
    monkeypatch.setattr(
        "experiments.candidates.capability_bound_semantic_currentness_learnability_r01.cli.run_registered",
        lambda path: path,
    )
    assert main(["run", "--manifest", str(target)]) == 0
    assert capsys.readouterr().out.strip() == str(target)
    assert not target.exists()  # patched runner performed no work or publication


def test_partial_publication_is_rejected(tmp_path) -> None:
    target = tmp_path / "result.json"
    with pytest.raises(ValueError, match="key/identity"):
        publish_complete_result(target, {"schema": "cbsc_lr01_complete_result_v1", "complete": True})
    assert not target.exists()


def test_atomic_mechanic_is_create_only(tmp_path) -> None:
    target = tmp_path / "mechanic.bin"
    assert _atomic_create_only_bytes(target, b"first") == target
    assert target.read_bytes() == b"first"
    with pytest.raises(FileExistsError, match="create-only"):
        _atomic_create_only_bytes(target, b"second")
    assert target.read_bytes() == b"first"
    assert not list(tmp_path.glob(".*cbsc-lr01-tmp-*"))


def _synthetic_incompetent_complete() -> dict:
    competence = []
    for block in range(4):
        competence.append({
            "purpose": "COMPETENCE", "block": block, "arm": "RAW_FLEX", "updates": 512,
            "optimizer_steps": 512, "examples": 49152, "finite_losses": True,
            "work_receipt": {
                "digest_role": "NON_AUTH_INFORMATIONAL_RECEIPT",
                "codec_context_materializations": 1536, "codec_xor_operations": 75264,
                "active_parameters": 43395, "parameter_bytes": 173580,
                "dense_macs_per_context": 43056, "training_forward_contexts": 49152,
                "backward_calls": 512, "adam_calls": 512,
                "scalar_target_exposures": 147456, "checkpoint_evaluations": 1,
                "evaluation_contexts": 768,
            },
            "checkpoints": [{
                "update": 512, "finite": True, "state_unchanged": True,
                "mean_regret": 0.1, "gated_regret": 0.1, "open_regret": 0.1,
                "correct": 767, "strict": 768, "zero_regret": 767,
            }],
        })
    schedules = describe()["representation"]["ordered_schedules"]
    return {
        "schema": "cbsc_lr01_complete_result_v1", "complete": True,
        "protocol_id": "CBSC-LR01", "codec_schedules": schedules,
        "branch": "RAW_INCOMPETENT",
        "audits": {
            "preflight_valid": True, "complete_competence_panel": True,
            "competence_numeric_health": True, "complete_main_panel": None,
            "main_numeric_health": None, "update_zero_common": None,
            "direct_pair_parity": None, "paired_work_parity": None,
        },
        "first_failing_witness": None,
        "preflight": {"valid": True, "ready_for_production": True, "codec_schedules": schedules},
        "competence": competence, "main": [], "decision": None,
        "work": {"competence_optimizer_steps": 2048, "main_optimizer_steps": 0, "threads": 1},
        "resource": {"wall_seconds": 1.0, "peak_rss_bytes": 1024},
    }


def _main_work_receipt() -> dict:
    return {
        "digest_role": "NON_AUTH_INFORMATIONAL_RECEIPT",
        "initial_parameter_digest": "display-only-init",
        "canonical_context_digest": "display-only-context",
        "encoded_context_digest": "arm-specific-display-only",
        "target_digest": "display-only-target",
        "batch_order_digest": "display-only-order",
        "initial_logits_zero": True,
        "codec_context_materializations": 1536, "codec_xor_operations": 75264,
        "active_parameters": 43395, "parameter_bytes": 173580,
        "dense_macs_per_context": 43056, "training_forward_contexts": 6144,
        "backward_calls": 64, "adam_calls": 64, "scalar_target_exposures": 18432,
        "checkpoint_evaluations": 5, "evaluation_contexts": 3840,
        "workers": 1, "threads": 1, "dtype": "float32",
    }


def _synthetic_complete_main() -> dict:
    base = _synthetic_incompetent_complete()
    for item in base["competence"]:
        item["checkpoints"][0].update(correct=768, strict=768, zero_regret=768, mean_regret=0.0)
    updates = [0, 8, 16, 32, 64]
    regrets = [0.5, 0.4, 0.3, 0.2, 0.1]
    main = []
    for block in range(24):
        arms = []
        for arm in ("STRUCTURED_CBSC", "STRUCTURED_SHAM", "RAW_FLEX"):
            arms.append({
                "purpose": "MAIN", "block": block, "arm": arm, "updates": 64,
                "optimizer_steps": 64, "examples": 6144, "finite_losses": True,
                "work_receipt": _main_work_receipt(),
                "checkpoints": [{
                    "update": update, "finite": True, "state_unchanged": True,
                    "mean_regret": regret, "gated_regret": regret, "open_regret": regret,
                    "correct": 768, "strict": 0, "zero_regret": 0,
                } for update, regret in zip(updates, regrets)],
            })
        correct_by_cell = [16] * 48
        toggle = {
            "neutral_active": [16, 16], "persist_refresh": [16, 16],
            "correct_swapped": [16, 16], "open_gated": [16, 16],
            "owner_live_broken": [16, 16], "authentic_reassociated": [16, 16],
        }
        main.append({
            "block": block, "arms": arms, "estimand": [0.0, 0.0, 0.0],
            "direct_pair_parity": True,
            "update_zero_common": True,
            "paired_work_parity": True,
            "structured_u64_correct_by_cell": correct_by_cell,
            "structured_toggle_counts": toggle,
            "structured_endpoint_gate": True,
        })
    decision = reduce_finite_panel([(0.0, 0.0, 0.0)] * 24)
    base.update(
        branch="PRACTICAL_EQUIVALENCE",
        audits={
            "preflight_valid": True, "complete_competence_panel": True,
            "competence_numeric_health": True, "complete_main_panel": True,
            "main_numeric_health": True, "update_zero_common": True,
            "direct_pair_parity": True, "paired_work_parity": True,
        },
        main=main,
        decision=to_jsonable(decision),
        work={"competence_optimizer_steps": 2048, "main_optimizer_steps": 4608, "threads": 1},
    )
    return base


def test_branch_coherent_complete_only_publication(tmp_path) -> None:
    result = _synthetic_incompetent_complete()
    validate_complete_result(result)
    target = tmp_path / "result.json"
    publish_complete_result(target, result)
    assert json.loads(target.read_text(encoding="ascii"))["branch"] == "RAW_INCOMPETENT"
    with pytest.raises(FileExistsError, match="create-only"):
        publish_complete_result(target, result)


def test_complete_validator_rejects_competence_identity_tamper() -> None:
    result = _synthetic_incompetent_complete()
    result["competence"][2]["block"] = 3
    with pytest.raises(ValueError, match="competence identity"):
        validate_complete_result(result)


def test_validator_recomputes_cell_toggles_and_rejects_coordinated_branch_tamper() -> None:
    result = _synthetic_complete_main()
    validate_complete_result(result)
    result["main"][0]["structured_toggle_counts"]["neutral_active"] = [15, 16]
    result["branch"] = "UNRESOLVED"
    with pytest.raises(ValueError, match="toggle map does not reconstruct"):
        validate_complete_result(result)


def test_validator_enforces_exact_checkpoint_regret_bounds() -> None:
    result = _synthetic_complete_main()
    result["main"][0]["arms"][0]["checkpoints"][0]["mean_regret"] = 11.0 / 8.0 + 0.01
    with pytest.raises(ValueError, match="outside exact bound"):
        validate_complete_result(result)


def test_post_activity_direct_parity_failure_publishes_coherent_invalid() -> None:
    result = _synthetic_complete_main()
    result["main"][0]["direct_pair_parity"] = False
    result["audits"]["direct_pair_parity"] = False
    result["branch"] = "INVALID"
    result["first_failing_witness"] = "direct_pair_parity"
    validate_complete_result(result)


def test_validator_rejects_struct_u64_cell_sum_tamper() -> None:
    result = _synthetic_complete_main()
    result["main"][0]["structured_u64_correct_by_cell"][0] = 15
    with pytest.raises(ValueError, match="do not sum"):
        validate_complete_result(result)


def test_literal_schedule_tamper_is_rejected_but_display_digest_is_not_a_gate() -> None:
    result = _synthetic_complete_main()
    result["main"][0]["arms"][1]["work_receipt"]["initial_parameter_digest"] = "different-display-only"
    validate_complete_result(result)
    result["codec_schedules"]["RAW_FLEX"][0] = [2, 0]
    with pytest.raises(ValueError, match="literal codec schedule"):
        validate_complete_result(result)


def test_main_numeric_health_failure_publishes_coherent_invalid() -> None:
    result = _synthetic_complete_main()
    result["main"][0]["arms"][0]["checkpoints"][2]["finite"] = False
    result["audits"]["main_numeric_health"] = False
    result["branch"] = "INVALID"
    result["first_failing_witness"] = "main_numeric_health"
    validate_complete_result(result)


def test_main_numeric_health_failure_rejects_coordinated_noninvalid_tamper() -> None:
    result = _synthetic_complete_main()
    result["main"][0]["arms"][0]["checkpoints"][2]["state_unchanged"] = False
    result["audits"]["main_numeric_health"] = False
    result["first_failing_witness"] = "main_numeric_health"
    result["branch"] = "PRACTICAL_EQUIVALENCE"
    with pytest.raises(ValueError, match="branch does not reconstruct"):
        validate_complete_result(result)


def test_invalid_branch_still_rejects_nonfinite_numeric_summary() -> None:
    result = _synthetic_complete_main()
    result["main"][0]["arms"][0]["checkpoints"][2]["finite"] = False
    result["main"][0]["arms"][0]["checkpoints"][2]["mean_regret"] = float("nan")
    result["audits"]["main_numeric_health"] = False
    result["branch"] = "INVALID"
    result["first_failing_witness"] = "main_numeric_health"
    with pytest.raises(ValueError, match="checkpoint regret mismatch"):
        validate_complete_result(result)
