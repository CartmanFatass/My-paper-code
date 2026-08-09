from __future__ import annotations

import copy
import base64
import hashlib
import json
import shutil
import subprocess
from pathlib import Path

import numpy as np
import pytest
import torch

from experiments.candidates.folr_core.counterfactual_witness_gated_nuisance_transfer import (
    ARMS,
    COMPLETE_RESET,
    ISOMORPHIC_GENERIC_MEMORY,
    MASTER_SEEDS,
    TECHNICAL_DECISION,
    TYPED_WITNESS_S03_S04,
    MatchedWitnessActor,
    _GzipJsonlWriter,
    _aggregate_metrics,
    _decision,
    _derive_seed,
    _episode_batch,
    _file_binding,
    _manifest_projection,
    _read_json,
    _read_jsonl_gz,
    _validate_episode,
    _write_json,
    analyze,
    build_frozen_manifest,
    evaluate,
    registered_config,
    technical_smoke_config,
    train,
    validate_evaluation,
    validate_result,
    validate_train,
)
from experiments.candidates.folr_core.counterfactual_witness_gated_nuisance_transfer_host import (
    CounterfactualWitnessHost,
    HostDimensions,
    StateProvenance,
)


SOURCE_COMMIT = "1" * 40


def _one_row(*, s: int, n_old: int, n_new: int, root: int = 91) -> dict[str, object]:
    return {
        "master_seed": MASTER_SEEDS[0],
        "phase": "evaluate",
        "episode": 0,
        "batch": None,
        "regime": "DIAGONAL" if n_old == n_new else "CHANGED",
        "counterfactual_pair_index": 0,
        "root": root,
        "s": s,
        "n_old": n_old,
        "n_new": n_new,
        "old_partner_key": "partner_a",
        "new_partner_key": "partner_b",
        "old_partner_role": "SCOUT",
        "new_partner_role": "RELAY",
        "action_uniform": 0.25,
        "rng_identity": {},
    }


def _actor() -> MatchedWitnessActor:
    config = technical_smoke_config()
    return MatchedWitnessActor(
        config=config,
        initialization_seed=_derive_seed(MASTER_SEEDS[0], "initialization"),
    )


def test_typed_route_binds_real_atomic_replacement_and_lineage_witness() -> None:
    actor = _actor()
    dimensions = HostDimensions()
    _, _, _, rows = _episode_batch(
        actor=actor,
        arm=TYPED_WITNESS_S03_S04,
        rows=[_one_row(s=1, n_old=0, n_new=1)],
        dimensions=dimensions,
    )
    row = rows[0]
    witness = row["membership_transaction"]
    assert witness["pre_keys"] == ("owner_t", "partner_a")
    assert witness["post_keys"] == ("owner_t", "partner_b")
    assert witness["same_owner_record"]
    assert witness["uninterrupted_owner_epoch"]
    assert witness["survivor_witness_passes"]
    assert witness["old_partner_witness_fails"]
    assert witness["s03_retained"]
    assert witness["old_s04_invalidated"]
    assert not witness["new_s04_rebuilt_after_event"]
    assert row["post_t2_routing_witness"]["new_s04_rebuilt_after_event"]
    assert witness["survivor_lineage"]["original_provenance"]["state_kind"] == "survivor_private"
    assert witness["old_partner_lineage"]["original_provenance"]["source_partner_key"] == "partner_a"
    assert witness["old_partner_lineage"]["substituted_provenance"]["source_partner_key"] == "partner_b"
    assert row["transition_two"]["new_partner_writer_digest"]
    assert row["terminal"]["all_memory_cleared"]


def test_typed_and_generic_are_tensor_exact_isomorphic_before_fixed_routing() -> None:
    config = registered_config()
    seed = _derive_seed(MASTER_SEEDS[0], "initialization")
    actors = [MatchedWitnessActor(config=config, initialization_seed=seed) for _ in ARMS]
    schemas = [actor.parameter_schema() for actor in actors]
    assert schemas[0] == schemas[1] == schemas[2]
    assert actors[0].parameter_count() == actors[1].parameter_count() == actors[2].parameter_count()
    for name in actors[0].state_dict():
        assert torch.equal(actors[0].state_dict()[name], actors[1].state_dict()[name])
    rows = [_one_row(s=0, n_old=1, n_new=0)]
    s = torch.tensor([0])
    n_old = torch.tensor([1])
    a = actors[0].transition_one(s, n_old)
    b = actors[1].transition_one(s, n_old)
    assert all(torch.equal(left, right) for left, right in zip(a, b))
    assert MatchedWitnessActor.CALL_TRACE == tuple(MatchedWitnessActor.CALL_TRACE)
    assert rows[0]["regime"] == "CHANGED"


def test_typed_route_fails_closed_on_partner_dependent_survivor_provenance() -> None:
    actor = _actor()
    row = _one_row(s=1, n_old=0, n_new=1)
    s = torch.tensor([1])
    n_old = torch.tensor([0])
    survivor, partner, initial, wait = actor.transition_one(s, n_old)
    host = CounterfactualWitnessHost(
        arm=TYPED_WITNESS_S03_S04,
        root=int(row["root"]),
        old_partner_key="partner_a",
        new_partner_key="partner_b",
        old_partner_role="SCOUT",
        new_partner_role="RELAY",
        dimensions=HostDimensions(),
    )
    bad_survivor = StateProvenance(
        state_kind="survivor_private",
        owner_lifecycle_key="owner_t",
        owner_membership_epoch=0,
        source_partner_key="partner_a",
        partner_dependencies=("partner_a",),
        writer_call_identity="t1:survivor_writer:bad",
        descriptor_digest="0" * 64,
    )
    partner_provenance = StateProvenance(
        state_kind="partner_scoped",
        owner_lifecycle_key="owner_t",
        owner_membership_epoch=0,
        source_partner_key="partner_a",
        partner_dependencies=("partner_a",),
        writer_call_identity="t1:partner_writer:ok",
        descriptor_digest="1" * 64,
    )
    host.transition_one(
        survivor_candidate=survivor[0],
        old_partner_candidate=partner[0],
        survivor_provenance=bad_survivor,
        old_partner_provenance=partner_provenance,
        wait_logit=wait[0],
    )
    descriptor = torch.zeros((1, technical_smoke_config().descriptor_dim))
    candidate = actor.learned_update(initial, torch.zeros_like(initial), descriptor)[0]
    with pytest.raises(RuntimeError, match="typed provenance"):
        host.apply_replacement(host.replacement_transaction(), learned_event_candidate=candidate)


def test_fixed_routes_have_exact_required_counterfactual_kernel_invariance() -> None:
    actor = _actor()
    dimensions = HostDimensions()
    typed_rows = [_one_row(s=1, n_old=value, n_new=0, root=101) for value in (0, 1)]
    _, _, _, typed = _episode_batch(
        actor=actor,
        arm=TYPED_WITNESS_S03_S04,
        rows=typed_rows,
        dimensions=dimensions,
    )
    assert typed[0]["final_kernel"]["probabilities_base64"] == typed[1]["final_kernel"]["probabilities_base64"]
    reset_rows = [_one_row(s=value, n_old=1, n_new=0, root=102) for value in (0, 1)]
    _, _, _, reset = _episode_batch(
        actor=actor,
        arm=COMPLETE_RESET,
        rows=reset_rows,
        dimensions=dimensions,
    )
    assert reset[0]["final_kernel"]["probabilities_base64"] == reset[1]["final_kernel"]["probabilities_base64"]
    assert all(len(row["final_kernel"]["probabilities"]) == 4 for row in typed + reset)


def test_manifest_freezes_diagonal_training_complete_eval_cube_and_full_caps() -> None:
    config = registered_config()
    manifest = build_frozen_manifest(config=config, source_commit=SOURCE_COMMIT, run_id="manifest-test")
    assert manifest["config"] == config.to_json()
    assert manifest["architecture"]["learned_arm_isomorphism"]["sole_delta"] == (
        "fixed_lifecycle_routing_after_identical_learned_candidates"
    )
    for seed in MASTER_SEEDS:
        assert len(manifest["training"][str(seed)]) == 32
        for batch in manifest["training"][str(seed)]:
            counts: dict[tuple[int, int, int], int] = {}
            for row in batch:
                key = (row["s"], row["n_old"], row["n_new"])
                counts[key] = counts.get(key, 0) + 1
            assert counts == {(0, 0, 0): 16, (0, 1, 1): 16, (1, 0, 0): 16, (1, 1, 1): 16}
        assert len(manifest["evaluation"][str(seed)]["DIAGONAL"]) == 512
        assert len(manifest["evaluation"][str(seed)]["CHANGED"]) == 512
    actor_runs = len(ARMS) * len(MASTER_SEEDS)
    assert actor_runs == 24
    assert actor_runs * 32 * 64 == 49152
    assert actor_runs * 32 == 768
    assert actor_runs * 2 * 512 == 24576
    assert (49152 + 24576) * 3 == 221184


def test_correct_action_probability_is_read_directly_from_full_kernel() -> None:
    actor = _actor()
    _, _, _, rows = _episode_batch(
        actor=actor,
        arm=ISOMORPHIC_GENERIC_MEMORY,
        rows=[_one_row(s=1, n_old=0, n_new=1)],
        dimensions=HostDimensions(),
    )
    row = rows[0]
    assert row["correct_action"] == 3
    assert row["correct_action_probability"] == row["final_kernel"]["probabilities"][3]
    assert row["reward"] in (0.0, 1.0)
    assert row["final_kernel"]["capture_sequence"] == 0
    assert row["sampling_chronology"]["action_sampling_sequence"] == 1
    assert row["sampling_chronology"]["chronology_token"] == row["final_kernel"]["chronology_token"]
    tampered = copy.deepcopy(row)
    tampered["transition_one"]["survivor_provenance"]["descriptor_digest"] = "f" * 64
    with pytest.raises(ValueError, match="provenance"):
        _validate_episode(tampered)
    tampered = copy.deepcopy(row)
    tampered["sampling_chronology"]["chronology_token"] = "f" * 64
    with pytest.raises(ValueError, match="chronology"):
        _validate_episode(tampered)


def _seed_metric(j: float, s: float, n: float, *, regime: str) -> dict[str, object]:
    return {
        "arm": "",
        "master_seed": 0,
        "regime": regime,
        "episodes": 0,
        "transitions": 0,
        "policy_calls": 0,
        "mean_return": j,
        "survivor_component_accuracy": s,
        "new_partner_component_accuracy": n,
        "mean_correct_action_probability": j,
    }


def _decision_fixture() -> tuple[dict[str, object], dict[str, object]]:
    metrics: dict[str, object] = {}
    for arm in ARMS:
        metrics[arm] = {}
        for regime in ("DIAGONAL", "CHANGED"):
            if arm == COMPLETE_RESET:
                j, s, n = 0.5, 0.5, 0.95
            else:
                j, s, n = 0.9, 0.95, 0.95
            seeds = []
            for index, seed in enumerate(MASTER_SEEDS):
                row = _seed_metric(j, s, n, regime=regime)
                row.update({"arm": arm, "master_seed": seed})
                seeds.append(row)
            metrics[arm][regime] = {
                "J": j,
                "S": s,
                "N": n,
                "correct_action_probability": j,
                "seeds": seeds,
            }
    pairs = {
        "FLIP_S_FIXED_N_OLD_N_NEW": {
            COMPLETE_RESET: {"all_kernel_byte_exact": True},
        },
        "FLIP_N_OLD_FIXED_S_N_NEW": {
            TYPED_WITNESS_S03_S04: {"all_kernel_byte_exact": True},
            ISOMORPHIC_GENERIC_MEMORY: {
                "max_correct_action_probability_difference": 0.0
            },
        },
    }
    return metrics, pairs


def _set_metric(
    metrics: dict[str, object], arm: str, regime: str, *, j: float, s: float | None = None, n: float | None = None
) -> None:
    slot = metrics[arm][regime]
    slot["J"] = j
    slot["S"] = j if s is None else s
    slot["N"] = j if n is None else n
    for row in slot["seeds"]:
        row["mean_return"] = j
        row["survivor_component_accuracy"] = slot["S"]
        row["new_partner_component_accuracy"] = slot["N"]


@pytest.mark.parametrize(
    ("case", "expected"),
    [
        ("invalid", "B2_INVALID"),
        ("reset", "RESET_LEAK_OR_NEW_PARTNER_CALIBRATION_FAILED"),
        ("generic_diag", "GENERIC_CAPACITY_CONTROL_FAILED"),
        ("typed_route", "TYPED_ROUTE_FAILED_ON_SUPPORT"),
        ("typed_value", "HOST_LOCAL_TYPED_FILTER_VALUE_SUPPORTED"),
        ("generic_equal", "GENERIC_MEMORY_SUFFICIENT_AT_CAP"),
        ("generic_out", "GENERIC_OUTGENERALIZES_TYPED"),
        ("both_fail", "OOD_LEARNABILITY_UNRESOLVED_AT_CAP"),
        ("mixed", "INDETERMINATE_AT_CAP"),
    ],
)
def test_all_nine_frozen_decision_branches_are_reachable_and_exclusive(
    case: str, expected: str
) -> None:
    metrics, pairs = _decision_fixture()
    valid = True
    if case == "invalid":
        valid = False
    elif case == "reset":
        _set_metric(metrics, COMPLETE_RESET, "CHANGED", j=0.60, s=0.60, n=0.95)
    elif case == "generic_diag":
        _set_metric(metrics, ISOMORPHIC_GENERIC_MEMORY, "DIAGONAL", j=0.70)
    elif case == "typed_route":
        _set_metric(metrics, TYPED_WITNESS_S03_S04, "DIAGONAL", j=0.70)
    elif case == "typed_value":
        _set_metric(metrics, TYPED_WITNESS_S03_S04, "CHANGED", j=0.90, s=0.95, n=0.95)
        _set_metric(metrics, ISOMORPHIC_GENERIC_MEMORY, "CHANGED", j=0.60)
    elif case == "generic_equal":
        _set_metric(metrics, TYPED_WITNESS_S03_S04, "CHANGED", j=0.82, s=0.92, n=0.92)
        _set_metric(metrics, ISOMORPHIC_GENERIC_MEMORY, "CHANGED", j=0.80, s=0.90, n=0.90)
    elif case == "generic_out":
        _set_metric(metrics, TYPED_WITNESS_S03_S04, "CHANGED", j=0.80, s=0.90, n=0.90)
        _set_metric(metrics, ISOMORPHIC_GENERIC_MEMORY, "CHANGED", j=0.88, s=0.92, n=0.92)
    elif case == "both_fail":
        _set_metric(metrics, TYPED_WITNESS_S03_S04, "CHANGED", j=0.70)
        _set_metric(metrics, ISOMORPHIC_GENERIC_MEMORY, "CHANGED", j=0.70)
    elif case == "mixed":
        _set_metric(metrics, TYPED_WITNESS_S03_S04, "CHANGED", j=0.82, s=0.92, n=0.92)
        _set_metric(metrics, ISOMORPHIC_GENERIC_MEMORY, "CHANGED", j=0.70)
    decision, gates = _decision(metrics, pairs, valid=valid)
    assert decision == expected
    assert sum(bool(value) for value in gates["terminal_predicates"].values()) <= 1
    if case == "generic_out":
        assert not gates["generic_equivalence"]
        assert gates["generic_outgeneralizes"]


def test_three_phase_technical_smoke_is_non_scientific_and_validated(tmp_path: Path) -> None:
    output = tmp_path / "smoke"
    external_result = tmp_path / "external" / "result.json"
    script = Path(__file__).resolve().parents[4] / "scripts" / "run_folr_b2_counterfactual_witness_gated_nuisance_transfer.py"
    python = "C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe"
    subprocess.run(
        [python, str(script), "train", "--output-root", str(output), "--source-commit", SOURCE_COMMIT,
         "--run-id", "folr-b2-technical-smoke", "--technical-smoke"],
        check=True,
    )
    subprocess.run([python, str(script), "evaluate", "--output-root", str(output)], check=True)
    subprocess.run(
        [python, str(script), "analyze", "--output-root", str(output), "--result", str(external_result)],
        check=True,
    )
    subprocess.run(
        [python, str(script), "validate-result", "--result", str(external_result),
         "--output-root", str(output), "--require-technical"],
        check=True,
    )
    train_summary = _read_json(output / "train_summary.json")
    evaluation = _read_json(output / "evaluation_summary.json")
    result = _read_json(output / "result.json")
    assert _read_json(external_result) == result
    assert train_summary["technical_only"]
    assert evaluation["technical_only"]
    assert result["technical_only"]
    assert not result["scientific_terminal_admitted"]
    assert result["decision"] == TECHNICAL_DECISION
    assert result["unique_frozen_branch"] is None
    assert validate_train(output, require_full=False)["artifact_kind"] == "FOLR_B2_TRAIN_SUMMARY"
    assert validate_evaluation(output, require_full=False)["artifact_kind"] == "FOLR_B2_EVALUATION_SUMMARY"
    assert validate_result(output / "result.json", require_full=False)["decision"] == TECHNICAL_DECISION
    with pytest.raises(ValueError, match="registered full"):
        validate_result(output / "result.json", require_full=True)
    assert result["activity_counts"] == {
        "actor_runs": 3,
        "train_episodes": 48,
        "eval_episodes": 96,
        "total_episodes": 144,
        "train_transitions_policy_calls": 144,
        "eval_transitions_policy_calls": 288,
        "total_environment_transitions": 432,
        "total_policy_calls": 432,
        "learner_calls": 3,
        "trainer_calls": 3,
        "optimizer_updates": 3,
        "k_search": 0,
        "hypothetical_transitions": 0,
    }

    manifest_tamper = tmp_path / "manifest-tamper"
    shutil.copytree(output, manifest_tamper)
    train_rows = list(_read_jsonl_gz(manifest_tamper / "train_episodes.jsonl.gz"))
    train_rows[0]["root"] += 1
    logits_bytes = base64.b64decode(train_rows[0]["final_kernel"]["logits_base64"])
    probability_bytes = base64.b64decode(
        train_rows[0]["final_kernel"]["probabilities_base64"]
    )
    coordinated_token = hashlib.sha256(
        b"FOLR-B2-KERNEL-CAPTURE\0"
        + _manifest_projection(train_rows[0])
        + b"\0"
        + logits_bytes
        + b"\0"
        + probability_bytes
    ).hexdigest()
    train_rows[0]["final_kernel"]["chronology_token"] = coordinated_token
    train_rows[0]["sampling_chronology"]["chronology_token"] = coordinated_token
    with _GzipJsonlWriter(manifest_tamper / "train_episodes.jsonl.gz") as writer:
        for row in train_rows:
            writer.write(row)
    tampered_train_summary = _read_json(manifest_tamper / "train_summary.json")
    tampered_train_summary["train_sidecar"] = _file_binding(
        manifest_tamper / "train_episodes.jsonl.gz", rows=len(train_rows)
    )
    _write_json(manifest_tamper / "train_summary.json", tampered_train_summary)
    with pytest.raises(ValueError, match="frozen manifest"):
        validate_train(manifest_tamper, require_full=False)

    metric_tamper = tmp_path / "metric-tamper"
    shutil.copytree(output, metric_tamper)
    tampered_evaluation = _read_json(metric_tamper / "evaluation_summary.json")
    tampered_evaluation["arm_runs"][0]["mean_return"] = 0.123
    _write_json(metric_tamper / "evaluation_summary.json", tampered_evaluation)
    tampered_result = _read_json(metric_tamper / "result.json")
    tampered_result["metrics"] = _aggregate_metrics(tampered_evaluation["arm_runs"])
    tampered_result["bindings"]["evaluation_summary"] = _file_binding(
        metric_tamper / "evaluation_summary.json"
    )
    _write_json(metric_tamper / "result.json", tampered_result)
    with pytest.raises(ValueError, match="do not recompute"):
        validate_result(metric_tamper / "result.json", require_full=False)

    pair_tamper = tmp_path / "pair-tamper"
    shutil.copytree(output, pair_tamper)
    pair_rows = list(_read_jsonl_gz(pair_tamper / "counterfactual_pairs.jsonl.gz"))
    pair_rows[0]["max_probability_difference"] += 0.01
    with _GzipJsonlWriter(pair_tamper / "counterfactual_pairs.jsonl.gz") as writer:
        for row in pair_rows:
            writer.write(row)
    tampered_result = _read_json(pair_tamper / "result.json")
    tampered_result["paired_counterfactual_sidecar"] = _file_binding(
        pair_tamper / "counterfactual_pairs.jsonl.gz", rows=len(pair_rows)
    )
    _write_json(pair_tamper / "result.json", tampered_result)
    with pytest.raises(ValueError, match="does not reconstruct"):
        validate_result(pair_tamper / "result.json", require_full=False)


def test_cli_help_exposes_only_frozen_lifecycle(tmp_path: Path) -> None:
    script = Path(__file__).resolve().parents[4] / "scripts" / "run_folr_b2_counterfactual_witness_gated_nuisance_transfer.py"
    completed = subprocess.run(
        ["C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe", str(script), "--help"],
        check=True,
        capture_output=True,
        text=True,
    )
    assert "train" in completed.stdout
    assert "evaluate" in completed.stdout
    assert "analyze" in completed.stdout
    assert "sweep" not in completed.stdout.lower()
