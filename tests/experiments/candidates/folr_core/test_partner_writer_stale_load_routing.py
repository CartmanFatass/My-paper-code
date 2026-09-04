from __future__ import annotations

import copy
from pathlib import Path
import subprocess

import pytest
import torch

from experiments.candidates.folr_core.partner_writer_stale_load_routing import (
    ARMS,
    COMPLETE_RESET,
    ISOMORPHIC_GENERIC_UPDATE,
    MASTER_SEEDS,
    TYPED_OWNER_EPOCH_ROUTING,
    MatchedRoutedActor,
    OrdinaryPartnerWriter,
    _aggregate_metrics,
    _contract_evidence,
    _decision,
    _derive_seed,
    _evaluate_one,
    _expected_counts,
    _GzipJsonlWriter,
    _phase_r_root_isolation,
    _read_json,
    _save_checkpoint,
    _summarize_phase_p_rows,
    _validate_lifecycle_witness,
    _write_json,
    build_frozen_manifest,
    generic_class_nesting_witness,
    registered_config,
    technical_smoke_config,
    validate_evaluation,
    validate_result,
    validate_train,
)
from experiments.candidates.folr_core.partner_writer_stale_load_routing_host import (
    HostDimensions,
    PartnerWriteDTO,
    PartnerWriterStaleLoadHost,
)


SOURCE_COMMIT = "1" * 40


def _actor() -> MatchedRoutedActor:
    writer = OrdinaryPartnerWriter(initialization_seed=101)
    return MatchedRoutedActor(frozen_writer_state=writer.state_dict(), initialization_seed=202)


def test_real_q0_to_q1_transaction_and_bound_writer_dto() -> None:
    host = PartnerWriterStaleLoadHost(root=19, regime="STALE_LOAD", dimensions=HostDimensions())
    owner = torch.tensor([0.2, -0.1])
    obsolete = torch.tensor([0.4, 0.3])
    host.transition_one(owner_state=owner, obsolete_partner_state=obsolete)
    witness = host.apply_replacement(host.replacement_transaction())
    assert witness.pre_keys == ("owner_t", "inert_partner_q0")
    assert witness.post_keys == ("owner_t", "inert_partner_q1")
    assert witness.owner_record_preserved and witness.owner_epoch_preserved
    assert witness.old_partner_state_invalidated and witness.new_partner_joined
    payload = torch.tensor([0.1, 0.2, 0.3, 0.4])
    dto = PartnerWriteDTO.make(writer_call_identity="test/write", source_bit=1, payload=payload)
    host.transition_two(dto)
    assert torch.equal(dto.materialize(device=torch.device("cpu")), payload)
    terminal = host.terminal_transition(action=3, target=3, action_count=4)
    assert terminal["reward"] == 1.0 and terminal["all_memory_cleared"]


def test_generic_class_contains_typed_transition_by_exact_mapping() -> None:
    actor = _actor()
    mapped = copy.deepcopy(actor)
    with torch.no_grad():
        mapped.event_update.weight[:, 2:4].zero_()
    s = torch.tensor([[1.0]])
    n_old = torch.tensor([[-1.0]])
    n_new = torch.tensor([[1.0]])
    typed, _ = actor.logits(arm=TYPED_OWNER_EPOCH_ROUTING, s=s, n_old=n_old, n_new=n_new)
    generic, _ = mapped.logits(arm=ISOMORPHIC_GENERIC_UPDATE, s=s, n_old=n_old, n_new=n_new)
    assert torch.equal(typed, generic)
    witness = generic_class_nesting_witness(actor)
    assert witness["constructive_containment"]
    assert "exact_zero" in witness["mapping"]["event_update.weight[:,2:4]"]


def test_three_arms_are_shape_count_initialization_and_writer_exact_matched() -> None:
    writer = OrdinaryPartnerWriter(initialization_seed=77)
    seed = _derive_seed(MASTER_SEEDS[0], "R/initialization")
    actors = [MatchedRoutedActor(frozen_writer_state=writer.state_dict(), initialization_seed=seed) for _ in ARMS]
    schemas = [actor.trainable_schema() for actor in actors]
    assert schemas[0] == schemas[1] == schemas[2]
    assert all(sum(row["count"] for row in schema) == sum(row["count"] for row in schemas[0]) for schema in schemas)
    for name in actors[0].state_dict():
        assert torch.equal(actors[0].state_dict()[name], actors[1].state_dict()[name])
        assert torch.equal(actors[0].state_dict()[name], actors[2].state_dict()[name])
    assert all(not parameter.requires_grad for parameter in actors[0].partner_writer.parameters())


def test_typed_old_partner_and_owner_epoch_interventions_are_exact() -> None:
    actor = _actor()
    row = {
        "master_seed": MASTER_SEEDS[0],
        "phase": "R_evaluate",
        "episode": 0,
        "batch": None,
        "regime": "STALE_LOAD",
        "s": 1,
        "n_old": 0,
        "n_new": 1,
        "root": 91,
        "action_uniform": 0.4,
        "rng_identity": {},
    }
    result = _evaluate_one(actor, TYPED_OWNER_EPOCH_ROUTING, row)
    assert result["do_n_old_flip_tv"] == 0.0
    assert result["kernel"]["probabilities_base64"] == result["do_n_old_flip_kernel"]["probabilities_base64"]
    assert result["owner_epoch_key_intervention_s_flip_tv"] == 0.0
    assert result["replacement"]["owner_epoch_preserved"]


def test_manifest_freezes_exact_balances_counts_caps_and_rng_namespaces() -> None:
    config = registered_config()
    manifest = build_frozen_manifest(config=config, source_commit=SOURCE_COMMIT, run_id="manifest-test")
    assert tuple(manifest["arms"]) == ARMS
    assert manifest["architecture"]["sole_treatment_difference"] == "fixed lifecycle input mask before identical event_update"
    for seed in MASTER_SEEDS:
        assert len(manifest["phase_p"][str(seed)]["train"]) == 32 * 64
        assert len(manifest["phase_p"][str(seed)]["evaluate"]) == 512
        rows = manifest["phase_r"][str(seed)][TYPED_OWNER_EPOCH_ROUTING]["train"]
        for batch in range(32):
            selected = [row for row in rows if row["batch"] == batch]
            assert sum(row["regime"] == "CLEAN" for row in selected) == 32
            assert sum(row["regime"] == "STALE_LOAD" for row in selected) == 32
            clean = {(row["s"], row["n_new"]) for row in selected if row["regime"] == "CLEAN"}
            stale = {(row["s"], row["n_old"], row["n_new"]) for row in selected if row["regime"] == "STALE_LOAD"}
            assert len(clean) == 4 and len(stale) == 8
        assert len(manifest["phase_r"][str(seed)][TYPED_OWNER_EPOCH_ROUTING]["evaluate"]) == 1024
    counts = _expected_counts(config, phase_r_ran=True)
    assert counts["training_episodes"] == 65536
    assert counts["evaluation_episodes"] == 28672
    assert counts["complete_episodes"] == 94208
    assert counts["environment_transitions"] == counts["policy_calls"] == 282624
    assert counts["learner_calls"] == counts["trainer_calls"] == counts["optimizer_updates"] == 1024
    namespaces = {
        row["rng_identity"]["namespace"]
        for row in manifest["phase_p"][str(MASTER_SEEDS[0])]["train"][:2]
        + manifest["phase_r"][str(MASTER_SEEDS[0])][TYPED_OWNER_EPOCH_ROUTING]["train"][:2]
    }
    assert len(namespaces) == 4
    arm_namespaces = {
        manifest["phase_r"][str(MASTER_SEEDS[0])][arm]["train"][0]["rng_identity"]["namespace"]
        for arm in ARMS
    }
    assert len(arm_namespaces) == 3
    all_root_sets = []
    for arm in ARMS:
        for phase in ("train", "evaluate"):
            roots = {row["root"] for row in manifest["phase_r"][str(MASTER_SEEDS[0])][arm][phase]}
            assert len(roots) == len(manifest["phase_r"][str(MASTER_SEEDS[0])][arm][phase])
            all_root_sets.append(roots)
    assert all(not left.intersection(right) for index, left in enumerate(all_root_sets) for right in all_root_sets[index + 1 :])
    assert _phase_r_root_isolation(manifest, config)


def _seed_metric(j: float, survivor: float, partner: float, *, arm: str, seed: int, regime: str, i: float = 0.0) -> dict[str, object]:
    return {
        "arm": arm,
        "master_seed": seed,
        "regime": regime,
        "episodes": 512,
        "J": j,
        "survivor_accuracy": survivor,
        "partner_accuracy": partner,
        "I_n_old": i,
        "n_old_kernel_byte_exact": i == 0.0,
        "s_kernel_byte_exact": arm == COMPLETE_RESET,
        "owner_epoch_key_intervention_removes_old_s": True,
    }


def _metrics() -> dict[str, object]:
    rows = []
    for arm in ARMS:
        for seed in MASTER_SEEDS:
            for regime in ("CLEAN", "STALE_LOAD"):
                if arm == COMPLETE_RESET:
                    rows.append(_seed_metric(0.475, 0.5, 0.95, arm=arm, seed=seed, regime=regime))
                else:
                    rows.append(_seed_metric(0.9, 0.95, 0.95, arm=arm, seed=seed, regime=regime))
    return _aggregate_metrics(rows)


@pytest.mark.parametrize(
    ("case", "branch"),
    [
        ("invalid", "B3_INVALID_CONTRACT"),
        ("calibration", "B3_PARTNER_WRITE_CALIBRATION_FAILED"),
        ("control", "B3_RESET_OR_CLEAN_CAPACITY_FAILED"),
        ("typed", "B3_TYPED_ROUTING_FAILED"),
        ("generic", "B3_GENERIC_SUFFICIENT_AT_CAP"),
        ("value", "B3_LOCAL_TYPED_ROUTING_VALUE_SUPPORTED"),
        ("indeterminate", "B3_INDETERMINATE_AT_CAP"),
    ],
)
def test_exact_seven_branch_precedence(case: str, branch: str) -> None:
    metrics = _metrics()
    valid = case != "invalid"
    calibration = case != "calibration"
    if case == "control":
        metrics[COMPLETE_RESET]["CLEAN"]["partner_accuracy"] = 0.8
    elif case == "typed":
        metrics[TYPED_OWNER_EPOCH_ROUTING]["STALE_LOAD"]["J"] = 0.7
    elif case == "value":
        metrics[ISOMORPHIC_GENERIC_UPDATE]["STALE_LOAD"]["J"] = 0.65
        metrics[ISOMORPHIC_GENERIC_UPDATE]["STALE_LOAD"]["I_n_old"] = 0.1
        metrics[ISOMORPHIC_GENERIC_UPDATE]["STALE_LOAD"]["n_old_kernel_byte_exact"] = False
        metrics[ISOMORPHIC_GENERIC_UPDATE]["D"] = 0.25
        metrics["Psi"] = 0.25
        metrics["seedwise_Psi"] = [0.25] * 8
    elif case == "indeterminate":
        metrics[ISOMORPHIC_GENERIC_UPDATE]["STALE_LOAD"]["J"] = 0.78
        metrics[ISOMORPHIC_GENERIC_UPDATE]["D"] = 0.12
        metrics["Psi"] = 0.12
        metrics["seedwise_Psi"] = [0.04] * 8
    evidence = {
        "valid": False,
        "first_failure_id": "C01_BINDING",
        "predicates": {"C01_BINDING": False},
    } if not valid else None
    decision, _ = _decision(valid=valid, calibration_passed=calibration, metrics=metrics if calibration and valid else None, contract_evidence=evidence)
    assert decision == branch


def test_invalid_contract_requires_structured_evidence_and_io_errors_are_not_converted() -> None:
    config = registered_config()
    manifest = build_frozen_manifest(config=config, source_commit=SOURCE_COMMIT, run_id="contract-mutation")
    mutated = copy.deepcopy(manifest)
    mutated["owner_binding"] = "wrong-owner@9"
    evidence = _contract_evidence(mutated, config)
    assert not evidence["valid"] and evidence["first_failure_id"] == "C01_BINDING"
    decision, gates = _decision(valid=False, calibration_passed=False, metrics=None, contract_evidence=evidence)
    assert decision == "B3_INVALID_CONTRACT"
    assert gates["first_failure_id"] == "C01_BINDING"
    with pytest.raises(ValueError, match="structured contract evidence"):
        _decision(valid=False, calibration_passed=False, metrics=None)
    malformed = copy.deepcopy(manifest)
    del malformed["architecture"]
    with pytest.raises(KeyError):
        _contract_evidence(malformed, config)


def test_retained_summary_and_lifecycle_mutations_are_detected() -> None:
    rows = [
        {"master_seed": 95031, "n_new": bit, "reward": 1.0, "n_new_flip_tv": 0.2, "kernel": {"probabilities_base64": f"k{bit}"}}
        for bit in (0, 1)
    ]
    summary = _summarize_phase_p_rows(rows)
    assert summary["aggregate_accuracy"] == 1.0 and summary["calibration_passed"]
    mutated = copy.deepcopy(rows)
    mutated[0]["reward"] = 0.0
    assert _summarize_phase_p_rows(mutated)["aggregate_accuracy"] == 0.5

    actor = _actor()
    row = {
        "master_seed": MASTER_SEEDS[0], "phase": "R_evaluate", "episode": 0, "batch": None,
        "regime": "STALE_LOAD", "s": 1, "n_old": 0, "n_new": 1, "root": 91,
        "action_uniform": 0.4, "rng_identity": {},
    }
    retained = _evaluate_one(actor, TYPED_OWNER_EPOCH_ROUTING, row)
    identity = f"R/{TYPED_OWNER_EPOCH_ROUTING}/{MASTER_SEEDS[0]}/0"
    _validate_lifecycle_witness(retained, writer_call_identity=identity)
    retained["replacement"]["old_partner_state_invalidated"] = False
    with pytest.raises(ValueError, match="replacement witness"):
        _validate_lifecycle_witness(retained, writer_call_identity=identity)


def test_stage_artifacts_are_write_once(tmp_path: Path) -> None:
    json_path = tmp_path / "artifact.json"
    _write_json(json_path, {"value": 1})
    with pytest.raises(FileExistsError, match="write-once"):
        _write_json(json_path, {"value": 2})
    sidecar = tmp_path / "rows.jsonl.gz"
    with _GzipJsonlWriter(sidecar) as writer:
        writer.write({"row": 1})
    with pytest.raises(FileExistsError, match="write-once"):
        with _GzipJsonlWriter(sidecar):
            pass
    checkpoint = tmp_path / "checkpoint.pt"
    _save_checkpoint(checkpoint, {"value": torch.tensor([1.0])})
    with pytest.raises(FileExistsError, match="write-once"):
        _save_checkpoint(checkpoint, {"value": torch.tensor([2.0])})


def test_one_technical_only_lifecycle_stops_naturally_or_validates_phase_r(tmp_path: Path) -> None:
    output = tmp_path / "run"
    result = tmp_path / "external" / "result.json"
    script = Path(__file__).resolve().parents[4] / "scripts" / "run_folr_b3_calibrated_partner_writer_stale_load_routing.py"
    python = "C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe"
    subprocess.run([python, str(script), "train", "--output-root", str(output), "--source-commit", SOURCE_COMMIT, "--run-id", "technical-only", "--technical-only"], check=True)
    subprocess.run([python, str(script), "evaluate", "--output-root", str(output)], check=True)
    subprocess.run([python, str(script), "analyze", "--output-root", str(output), "--result", str(result)], check=True)
    train_summary = validate_train(output, require_full=False)
    validate_evaluation(output, require_full=False)
    validated = validate_result(result, output_root=output, require_full=False)
    assert validated["decision"] == "TECHNICAL_ONLY_NO_SCIENTIFIC_DECISION"
    assert validated["unique_frozen_branch"] is None
    assert not validated["scientific_terminal_admitted"]
    assert train_summary["phase_r_ran"] == train_summary["phase_p_evaluation"]["calibration_passed"]
    assert train_summary["activity_counts"]["registered_fulls"] == 0
    assert train_summary["activity_counts"]["retries"] == 0


def test_cli_help_has_no_retry_rescue_sweep_or_checkpoint_selector() -> None:
    script = Path(__file__).resolve().parents[4] / "scripts" / "run_folr_b3_calibrated_partner_writer_stale_load_routing.py"
    completed = subprocess.run(["C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe", str(script), "--help"], check=True, capture_output=True, text=True)
    lowered = completed.stdout.lower()
    assert "train" in lowered and "evaluate" in lowered and "analyze" in lowered
    assert "retry" not in lowered and "rescue" not in lowered and "sweep" not in lowered
