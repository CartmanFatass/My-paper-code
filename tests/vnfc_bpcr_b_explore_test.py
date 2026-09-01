from __future__ import annotations

import ast
import copy
from contextlib import nullcontext
from dataclasses import replace
from datetime import datetime, timezone
import inspect
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import pytest
import torch

import scripts.run_vnfc_bpcr_b_explore as subject
from experiments.candidates.variable_n_fleet_churn_b_explore import derive_recovery_telemetry, expected_host_call_inventory


NOW = datetime(2026, 9, 1, 12, 0, tzinfo=timezone.utc)


class Sink:
    schema = subject.TELEMETRY_SCHEMA
    fields = tuple(subject.REQUIRED_TELEMETRY_FIELDS)

    def emit(self, payload: object) -> None:
        self.payload = payload


def receipt(**updates: object) -> dict[str, object]:
    value = {
        "schema_version": 1,
        "captured_at": "2026-09-01T11:59:00Z",
        "assessed_at": "2026-09-01T11:59:01Z",
        "minimum_available_bytes": 4 * 1024**3,
        "available_physical_bytes": 6 * 1024**3,
        "effective_available_bytes": 5 * 1024**3,
        "physical_floor_pass": True,
        "effective_floor_pass": True,
        "passed": True,
    }
    value.update(updates)
    return value


def telemetry(**updates: object) -> dict[str, object]:
    value = {field: 1 for field in subject.REQUIRED_TELEMETRY_FIELDS}
    value.update({
        "telemetry_schema": subject.TELEMETRY_SCHEMA, "telemetry_terminal": True,
        "stage_wall_seconds": {stage: 1.0 for stage in ("source_binding", "training", "evaluation", "serialization")},
        "stage_cpu_seconds": {stage: 1.0 for stage in ("source_binding", "training", "evaluation", "serialization")},
        "available_physical_bytes": 6 * 1024**3, "effective_available_bytes": 5 * 1024**3,
        "parameter_count_by_arm": {arm: 1 for arm in subject.ARMS},
        "forward_calls_by_arm": {arm: 1 for arm in subject.ARMS},
        "backward_calls_by_arm": {arm: 1 for arm in subject.ARMS},
        "flop_exposure_by_arm": {arm: 1 for arm in subject.ARMS},
        "primary_host_calls": 1, "shadow_host_calls": 1, "total_host_call_multiplier": 2.0,
        "measurement_source": "Windows Toolhelp/Process/PSAPI process-tree sampling",
        "performance_evidence": True,
        "measurement_limitations": ("finite sampling",), "sample_interval_seconds": .05, "sample_count": 2,
        "preflight_binding": {"schema_version": 1, "receipt_sha256": "d" * 64, "captured_at": "2026-09-01T11:59:00Z", "assessed_at": "2026-09-01T11:59:01Z", "age_seconds_at_monitor_start": 60.0, "available_physical_bytes": 6 * 1024**3, "effective_available_bytes": 5 * 1024**3},
        "stage_observation_count": {stage: 1 for stage in ("source_binding", "training", "evaluation", "serialization")},
        "cpu_core_equivalents": 1.0, "host_cpu_occupancy": .5, "logical_processor_count": 2,
        "peak_process_count": 1, "peak_thread_count": 1, "scientific_work_transitions": 1,
        "io_other_bytes": 0, "aggregate_io_bytes": 2,
        "implementation_ready": True, "performance_readiness": "READY", "implementation_blocker": None,
        "storage_high_water_disposition": "EXACT_R01_MONOTONIC_CREATE_ONLY", "scratch_peak_bytes": 0,
        "durable_peak_bytes": 1, "durable_directory_total_bytes": 1,
        "durable_artifact_inventory": ({"relative_path": "STARTED.json", "size_bytes": 1, "sha256": "f" * 64},),
        "frozen_native_artifact_inventory": ({"path": "native.dll", "size_bytes": 1, "sha256": "a" * 64},),
    })
    value.update(updates)
    return value


def bound_telemetry(terminal: dict[str, object], **updates: object) -> dict[str, object]:
    exposure = terminal["exposure"]; training = terminal["training"]
    value = telemetry(
        parameter_count_by_arm={arm: training[arm]["parameter_count"] for arm in subject.ARMS},
        forward_calls_by_arm={arm: exposure["training"][arm]["action_selection_forward_calls"] + exposure["training"][arm]["optimizer_forward_calls"] + exposure["evaluation"][arm]["policy_forward_calls"] + exposure["evaluation"][arm]["diagnostic_forward_calls"] for arm in subject.ARMS},
        backward_calls_by_arm={arm: exposure["training"][arm]["backward_calls"] for arm in subject.ARMS},
        primary_host_calls=terminal["host_call_ledger"]["primary_total"],
        shadow_host_calls=terminal["host_call_ledger"]["shadow_total"],
    )
    value.update(updates); return value


def source_identity_fixture() -> dict[str, object]:
    digest = lambda label: hashlib.sha256(label.encode()).hexdigest()
    included = {"b_adapter_source_sha256": digest("b-source"), "included_r09_header_sha256": digest("header"), "transitive_r09_checker_sha256": digest("checker"), "registered_r09_source_sha256": digest("r09-source")}
    return {"mode": "current_checkout_actual_bytes", "files": (), "native_artifact": {"path": str((Path.cwd() / "primary.dll").resolve()), "sha256": digest("primary"), "size": 1, "build_key": digest("primary-build"), "source_sha256": digest("r09-source")}, "shadow_native_artifact": {"artifact_path": str((Path.cwd() / "shadow.dll").resolve()), "artifact_sha256": digest("shadow"), "artifact_size": 1, "build_key": digest("build"), "source_identity": included, "registered_r09_artifact_path": str((Path.cwd() / "primary.dll").resolve()), "registered_r09_artifact_sha256": digest("primary"), "registered_r09_build_key": digest("primary-build")}}


def shadow_receipt(batch_id: str) -> dict[str, object]:
    digest = lambda label: hashlib.sha256(label.encode()).hexdigest()
    outer = source_identity_fixture(); shadow = outer["shadow_native_artifact"]; primary = outer["native_artifact"]
    source = {"included_source_identity": shadow["source_identity"], "shadow_build_key": shadow["build_key"], "shadow_embedded_build_key": shadow["build_key"], "shadow_artifact_path": shadow["artifact_path"], "shadow_artifact_sha256": shadow["artifact_sha256"], "primary_artifact_path": primary["path"], "primary_artifact_sha256": primary["sha256"], "primary_registered_build_key": primary["build_key"]}
    boundaries = tuple({"boundary_index": index, "command_digest": digest(f"command-{index}"), "cumulative_action_digest": digest(f"cumulative-{index}"), "primary_full_output_digest": digest(f"output-{index}"), "shadow_full_output_digest": digest(f"output-{index}"), "exact": True, "primary_integrated_ticks": tuple([140 + 20 * index] * 8), "shadow_integrated_ticks": tuple([140 + 20 * index] * 8), "shadow_ticks_per_session": (20,) * 8, "shadow_tick_rows_digest": digest(f"ticks-{index}"), "source_exact_pre_post": True} for index in range(6))
    sensitivity_calls = 1 if "/N7z" in batch_id and not batch_id.endswith("/BCRH") else 0; bcrh_calls = 6 if batch_id.endswith("/BCRH") else 0
    authority = {"scientific_trajectory_source": "registered_r09_native_interactive_primary", "action_source": "single_paired_caller_command_forwarded_unchanged", "scientific_return_source": "registered_r09_native_interactive_primary", "shadow_effect": "read_only_deterministic_replay_telemetry"}
    paired = {"schema": "VNFC-BEXP-PAIRED-PRIMARY-SHADOW-RECEIPT-v1", "input_digest": digest("input"), "action_digest": boundaries[-1]["cumulative_action_digest"], "width": 8, "main_return_source": "registered_r09_native_interactive_primary", "shadow_role": "telemetry_only_no_action_or_return_authority", "authority": authority, "host_call_ledger": expected_host_call_inventory(paired_steps=6, primary_sensitivity_calls=sensitivity_calls, primary_bcrh_calls=bcrh_calls), "initial": {"primary_full_output_digest": digest("initial"), "shadow_full_output_digest": digest("initial"), "exact": True}, "source_pre": source, "source_post": dict(source), "boundaries": boundaries, "incomplete": False, "last_failure": None}
    raw_ticks = tuple({"post_loss_second": index, "tick_end_second": index + 1, "integrated_ticks": index + 1, "zone1_delivery": 1, "zone2_delivery": 1, "failed_zone_delivery": int(index == 0), "failed_zone_executor_state_before": 0, "failed_zone_executor_rank_before": None, "failed_zone_executor_acquisition_elapsed_before": index, "failed_zone_executor_state_after": 0, "failed_zone_executor_rank_after": None, "failed_zone_executor_acquisition_elapsed_after": index + 1, "acquisition_transition": index == 0} for index in range(120))
    recovery = derive_recovery_telemetry(raw_ticks)
    final_shadow = tuple({"interactive": {"terminal": True}, "tick_rows": tuple({"integrated_ticks": 101 + index} for index in range(20)), "receipt": dict(recovery)} for _ in range(8))
    return subject.build_shadow_receipt(batch_id, paired, final_shadow)


def configs() -> tuple[subject.BExploreRunConfig, ...]:
    return (
        subject.BExploreRunConfig(subject.DEBUG_STAGE, subject.DEBUG_SEED, 8),
        *(subject.BExploreRunConfig(subject.PRIMARY_STAGE, seed, 64) for seed in subject.PRIMARY_SEEDS),
        subject.BExploreRunConfig(subject.OPTIONAL_STAGE, subject.OPTIONAL_SEEDS[0], 64, "training_variance", "N3_N5_TRAINING_ONLY"),
        subject.BExploreRunConfig(subject.OPTIONAL_STAGE, subject.OPTIONAL_SEEDS[1], 64, "technical_issue", "TECHNICAL_PRE_N7"),
    )


def invocation_roots(base: Path, config: subject.BExploreRunConfig) -> tuple[Path, Path, Path]:
    return base / "scratch", base / "durable" / subject.RUN_REVISION / config.stage / str(config.seed), base / "publication"


def checkpoint_artifact(config: subject.BExploreRunConfig) -> dict[str, object]:
    digest = "c" * 64
    return {"schema": "VNFC_BPCR_BEXP_R01_CHECKPOINT_MANIFEST_V1", "namespace": config.namespace, "bundle_filename": "CHECKPOINTS.bin", "bundle_sha256": digest, "bundle_size": 1, "checkpoint_identities": {arm: {label: digest for label in subject.CHECKPOINTS} for arm in subject.ARMS}, "contents": [{"arm": "MAPR", "checkpoint": "initial", "name": "p", "dtype": "float64", "shape": [1], "bytes": 8, "sha256": digest}], "manifest_filename": "CHECKPOINTS_MANIFEST.json", "manifest_sha256": digest}


def ps_b0_artifact(config: subject.BExploreRunConfig) -> dict[str, object]:
    return {"schema": "VNFC_BPCR_BEXP_R01_PS_B0_ARTIFACT_IDENTITY_V1", "namespace": config.namespace, "filename": "PS_B0.json", "sha256": "e" * 64, "comparisons": 288, "primary_only_host_calls": 24}


def ps_host_call_ledger() -> dict[str, object]:
    records = []
    for n in subject.ROSTERS:
        for zone in subject.ZONES:
            for family, operations in (("t0_and_later", ("reset", "bcrh", "step")), ("diagnostic", ("reset",))):
                for operation in operations:
                    records.append({"ordinal": len(records) + 1, "roster_size": n, "failed_zone": zone, "state_family": family, "operation": operation, "batch_width": 8, "unique_presentation_surfaces": 4, "duplicates_per_surface": 2, "duplicate_exact_required": True, "primary_only": True, "result_bearing": False})
    return {"schema": "VNFC_BPCR_BEXP_R01_PS_B0_PRIMARY_HOST_CALL_LEDGER_V1", "records": tuple(records), "primary_only_host_calls": 24, "reset_calls": 12, "bcrh_calls": 6, "step_calls": 6, "batch_widths": (8,), "scientific_values_exposed": False}


def durable_ps_b0_artifact(root: Path, config: subject.BExploreRunConfig) -> dict[str, object]:
    rows = []
    source_identity = {"schema": "fixture-source", "sha256": "9" * 64}
    for n, zone, kind, presentation, checkpoint, arm in sorted(subject.ps_b0_expected_addresses(), key=str):
        command = (0, 1, None, None); diagnostic = kind == "diagnostic_null_tie"
        trace_tokens = []
        decoder_tokens = []
        for token in range(4):
            probability = (1.0 / (n + 1)).hex(); trace_candidates = [] ; decoder_candidates = []
            for rank in (*range(n), None):
                trace_candidate = {"physical_rank": rank, "available_before": True, "environment_legal": True, "masked_support": True, "base_logit_binary64": 0.0.hex(), "prefix_conditioned_logit_binary64": 0.0.hex(), "masked_logit_binary64": 0.0.hex(), "probability_binary64": probability, "opaque_tie_rank": 2**30 if rank is None else rank}
                trace_candidates.append(trace_candidate)
                scores = {field: trace_candidate[field] for field in ("base_logit_binary64", "prefix_conditioned_logit_binary64", "masked_logit_binary64", "probability_binary64")}
                decoder_candidates.append({"physical_rank": rank, "canonical": dict(scores), "tested": dict(scores), "differences": {"base_logit_difference_binary64": 0.0.hex(), "prefix_conditioned_logit_difference_binary64": 0.0.hex(), "masked_logit_difference_binary64": 0.0.hex(), "probability_difference_binary64": 0.0.hex()}, "support_equal": True, "opaque_tie_rank_equal": True})
            trace_tokens.append({"model_token": token, "physical_token": token, "prefix_physical_choices": (), "candidates": tuple(trace_candidates), "selected_physical_rank": command[token]})
            decoder_tokens.append({"physical_token": token, "canonical_prefix_physical_choices": (), "tested_prefix_physical_choices": (), "candidates_by_physical_rank": tuple(decoder_candidates)})
        trace = {"origin": "fixture", "native_epoch": 0, "native_token_state": (0, 0, 0, 0), "native_token_elapsed": (0, 0, 0, 0), "fixed_physical_occupants_model_order": (-1, -1, -1, -1), "tokens": tuple(trace_tokens), "forward_command_rows": command, "inverse_mapped_physical_command": command, "forward_verified_exact": True, "forcing": "deterministic_opaque_tie_decoder"}
        if diagnostic: trace = {**trace, "diagnostic_predecision_support": {"target_physical_token": 0, "target_legal_physical_agent_ranks": (0, 1), "target_legal_agent_count": 2, "target_null_legal": True}}
        copermutation = {"agent_rows_by_physical_rank": tuple(range(n)), "legal_masks_by_physical_rank": tuple((True,) * 4 for _ in range(n)), "fixed_occupants_physical": (-1, -1, -1, -1), "opaque_ranks_by_physical_rank": {rank: rank for rank in range(n)}, "prefix_conditioned_physical_support": tuple(tuple((*range(n), None)) for _ in range(4)), "diagnostic_predecision_target_support": (0, 1) if diagnostic else ()}
        decoder = {"schema": "VNFC_BPCR_BEXP_R01_PS_B0_ALIGNED_SCORE_PROBABILITY_DIFF_V1", "alignment": "physical_token_then_physical_candidate_rank", "tokens": tuple(decoder_tokens), "maximum_absolute_probability_difference_binary64": 0.0.hex(), "physical_command_equal": True}
        rows.append({"roster_size": n, "failed_zone": zone, "state_kind": kind, "presentation": presentation, "checkpoint": checkpoint, "arm": arm, "agent_rows_copermuted": True, "legal_masks_copermuted": True, "fixed_occupants_copermuted": True, "opaque_ranks_copermuted": True, "physical_support_equal": True, "canonical_physical_command": command, "inverse_mapped_physical_command": command, "null_case_present": diagnostic, "fixed_or_acquiring_case_present": kind == "later_fixed_or_acquiring", "null_action_legal": diagnostic, "legal_agent_candidate_count": 2 if diagnostic else 0, "diagnostic_target_physical_token": 0 if diagnostic else None, "predecision_legal_agent_count": 2 if diagnostic else 0, "opaque_deterministic_tie_ranks_complete": True, "equal_logit_claim": False, "presentation_path": "fixture", "canonical_presentation_order": tuple(range(n)), "tested_presentation_order": tuple(range(n)), "native_physical_transition_command": None, "canonical_trace": trace, "tested_trace": copy.deepcopy(trace), "copermutation_diagnostics": {"canonical": copermutation, "tested": copy.deepcopy(copermutation)}, "score_probability_difference_diagnostics": {"deterministic_decoder": decoder, "diagnostic_support_semantics": "actual_state_predecision_target_token" if diagnostic else None}, "model_identity": {"arm": arm, "class": arm, "state_sha256": hashlib.sha256(f"{checkpoint}/{arm}".encode()).hexdigest(), "tensors": ()}, "source_identity": source_identity})
    summary = subject._validate_serialized_ps_b0_rows(rows)
    payload = {"schema": "VNFC_BPCR_BEXP_R01_PS_B0_ARTIFACT_V1", "namespace": config.namespace, "comparisons": tuple(rows), "summary": summary, "host_call_ledger": ps_host_call_ledger()}
    path = subject._create_once_json(subject.named_output_directory(root, config) / "PS_B0.json", payload)
    return {"schema": "VNFC_BPCR_BEXP_R01_PS_B0_ARTIFACT_IDENTITY_V1", "namespace": config.namespace, "filename": path.name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "comparisons": 288, "primary_only_host_calls": 24}


def durable_checkpoint_artifact(root: Path, config: subject.BExploreRunConfig) -> dict[str, object]:
    checkpoints = {}
    for arm_index, arm in enumerate(subject.ARMS):
        checkpoints[arm] = {}
        for label_index, label in enumerate(subject.CHECKPOINTS):
            model = torch.nn.Linear(2, 1, dtype=torch.float64)
            with torch.no_grad(): model.weight.fill_(arm_index + label_index + 1); model.bias.fill_(label_index)
            checkpoints[arm][label] = subject.clone_checkpoint(model, label)
    return subject._serialize_checkpoint_bundle_once(root, config, checkpoints)


def durable_three_artifact_bundle(scientific_root: Path, publication_root: Path, config: subject.BExploreRunConfig, terminal: dict[str, object]) -> tuple[Path, dict[str, object]]:
    body_identity = subject._serialize_result_body_once(scientific_root.parents[2], config, terminal)
    rows = []
    for path in sorted(scientific_root.iterdir(), key=lambda item: item.name):
        if path.is_file():
            payload = path.read_bytes()
            rows.append({"relative_path": path.name, "size_bytes": len(payload), "sha256": hashlib.sha256(payload).hexdigest()})
    storage = {"storage_high_water_disposition": "EXACT_R01_MONOTONIC_CREATE_ONLY", "durable_directory_total_bytes": sum(row["size_bytes"] for row in rows), "durable_artifact_inventory": tuple(rows), "directory_inventory": (), "valid": True}
    telemetry_payload = bound_telemetry(terminal)
    telemetry_doc = {"schema": "VNFC_BPCR_BEXP_R01_TELEMETRY_TERMINAL_V1", "namespace": config.namespace, "scientific_body": {"relative_path": "RESULT_BODY.json", "size_bytes": body_identity["size_bytes"], "sha256": body_identity["sha256"]}, "scientific_storage_seal": storage, "telemetry": telemetry_payload}
    publication_root.mkdir(parents=True)
    telemetry_bytes = json.dumps(telemetry_doc, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    telemetry_path = publication_root / "TELEMETRY_TERMINAL.json"; telemetry_path.write_bytes(telemetry_bytes)
    claim = {"schema": "VNFC_BPCR_BEXP_R01_VALID_CLAIM_V1", "namespace": config.namespace, "scientific_body_relative_path": "RESULT_BODY.json", "scientific_body_size_bytes": body_identity["size_bytes"], "scientific_body_sha256": body_identity["sha256"], "scientific_storage_seal_sha256": subject._canonical_digest(storage), "telemetry_relative_path": "TELEMETRY_TERMINAL.json", "telemetry_size_bytes": len(telemetry_bytes), "telemetry_sha256": hashlib.sha256(telemetry_bytes).hexdigest()}
    claim_path = publication_root / "VALID_CLAIM.json"; claim_path.write_bytes(json.dumps(claim, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8"))
    return claim_path, body_identity


def runtime_terminal(config: subject.BExploreRunConfig, artifact: dict[str, object] | None = None, ps_artifact: dict[str, object] | None = None) -> dict[str, object]:
    counts = subject.expected_counts(config)
    loss = {"actor_loss": 0.0, "critic_loss": 0.0, "entropy_loss": 0.0, "total_loss": 0.0, "preclip_gradient_norm": 0.0, "policy_entropy": 0.0}
    training = {}
    for arm in subject.ARMS:
        updates = tuple({"episodes": 16, "joint_transitions": 96, "optimizer_steps": 16, "training_action_forward_calls": 12, "optimizer_forward_calls": 384, "backward_calls": 16, "finite_values": True, "training_J_ext": (0.5,) * 16, "return_variance": 0.0, "advantage_variance": 0.0, "loss_rows": tuple(dict(loss) for _ in range(16)), "shadow_receipts": (shadow_receipt(f"{config.namespace}/TRAIN/{arm}/u{update}/N3"), shadow_receipt(f"{config.namespace}/TRAIN/{arm}/u{update}/N5")), "nonfinite_update_count": 0} for update in range(config.updates))
        training[arm] = {"updates": config.updates, "episodes": counts["training_episodes_per_arm"], "joint_transitions": counts["joint_transitions_per_arm"], "optimizer_steps": counts["optimizer_steps_per_arm"], "parameter_count": 1, "training_action_forward_calls": 12 * config.updates, "optimizer_forward_calls": 384 * config.updates, "backward_calls": 16 * config.updates, "finite_values": True, "nonfinite_update_count": 0, "updates_telemetry": updates}
    learned = []
    checkpoints = ("final",) if config.stage == subject.DEBUG_STAGE else subject.CHECKPOINTS
    endpoint = {"fail_endpoint": (1, 2), "total_endpoint": (3, 4), "intact_endpoint": (2, 3)}
    for n in subject.ROSTERS:
        for zone in subject.ZONES:
            for label in checkpoints:
                for arm in subject.ARMS:
                    n7 = n == 7; direct = arm == "DIRECT"
                    cell = f"N{n}z{zone}"
                    learned.append({"arm": arm, "checkpoint": label, "cell": cell, "rollouts": 8, "relabel_mismatch_count": 0, "hard_valid": True, "finite_values": True, "evaluation_policy_forward_calls": 6, "diagnostic_forward_calls": 60 if direct else 48, "action_sensitivity": tuple({"world": row, "candidate_count": 2, "min_c60": 0, "max_c60": 6, "sensitive": True} for row in range(8)) if n7 else (), "action_sensitivity_status": "OBSERVED_TREATMENT_BLIND_N7" if n7 else "NOT_APPLICABLE_TRAIN_SUPPORT_CELL", "direct_residual_activity": tuple({"boundary": row // 8, "world_row": row % 8, "total_variation": 0.0, "physical_command_change": False, "status": "OBSERVED_DIRECT_ABLATION"} for row in range(48)) if direct else (), "direct_residual_activity_status": "OBSERVED_DIRECT_ABLATION" if direct else "NOT_APPLICABLE_MAPR", "endpoints": tuple(dict(endpoint) for _ in range(8)), "shadow_receipts": (shadow_receipt(f"{config.namespace}/{cell}/{label}/{arm}"),)})
    checker = {"candidate_count": 1, "scorer_command": (None, None, None, None), "checker_command": (None, None, None, None), "scorer_checker_equal": True, "independent_enumerator_equal": True, "post60_reduced": True, "floor": (0, 1), "releases": 0, "objective_limbs": (0, 0, 0, 0), "checker_objective_limbs": (0, 0, 0, 0), "candidate_digest": 1, "checker_digest": 1}
    bcrh = tuple({"arm": "BCRH", "cell": f"N7z{zone}", "rollouts": 8, "comparison_status": "IDENTIFIED", "hard_valid": True, "finite_values": True, "evaluation_policy_forward_calls": 0, "diagnostic_forward_calls": 0, "checker_rows": tuple(dict(checker) for _ in range(48)), "endpoints": tuple(dict(endpoint) for _ in range(8)), "shadow_receipts": (shadow_receipt(f"{config.namespace}/N7z{zone}/BCRH"),)} for zone in subject.ZONES)
    evaluation = {"learned": tuple(learned), "bcrh": bcrh, "rollouts": counts["evaluation_rollouts_total"], "relabel_mismatch_count": {"MAPR": 0, "DIRECT": 0}}
    receipts = tuple(receipt for arm in subject.ARMS for update in training[arm]["updates_telemetry"] for receipt in update["shadow_receipts"]) + tuple(receipt for row in (*evaluation["learned"], *evaluation["bcrh"]) for receipt in row["shadow_receipts"])
    groups = 6 if config.stage == subject.DEBUG_STAGE else 12
    exposure = {"training": {arm: {"action_selection_forward_calls": 12 * config.updates, "optimizer_forward_calls": 384 * config.updates, "backward_calls": 16 * config.updates} for arm in subject.ARMS}, "evaluation": {"MAPR": {"policy_forward_calls": 6 * groups, "diagnostic_forward_calls": 48 * groups}, "DIRECT": {"policy_forward_calls": 6 * groups, "diagnostic_forward_calls": 60 * groups}, "BCRH": {"policy_forward_calls": 0, "diagnostic_forward_calls": 0}}}
    return {
        "schema": "VNFC_BPCR_BEXP_R01_RUNTIME_TERMINAL_V1", "namespace": config.namespace,
        "counts": counts, "ps_b0_passed": True,
        "learned_relabel_mismatch_count": {"MAPR": 0, "DIRECT": 0},
        "common_host_hard_valid": True, "finite_values": True,
        "initial_final_checkpoints_retained": True, "n7_controls_frozen_before_open": True,
        "source_identity": source_identity_fixture(), "source_pre_digest": subject._canonical_digest(source_identity_fixture()), "source_post_digest": subject._canonical_digest(source_identity_fixture()),
        "shadow_boundary_exact": True, "shadow_source_stable": True,
        "shadow_influenced_actions": False, "observations_complete": True,
        "training_observation_rows": counts["training_episodes_total"],
        "individual_world_seed_rows": counts["evaluation_rollouts_total"],
        "optimization_rows": counts["optimizer_steps_total"],
        "bcrh_comparison_status": "IDENTIFIED",
        "shadow_receipts": receipts, "ps_b0_host_call_ledger": ps_host_call_ledger() if config.stage == subject.DEBUG_STAGE else None, "host_call_ledger": subject._combined_host_call_ledger(config, subject._aggregate_host_call_ledger(receipts), ps_host_call_ledger() if config.stage == subject.DEBUG_STAGE else None), "training": training, "evaluation": evaluation,
        "exploratory_readout": subject._exploratory_readout(config, evaluation),
        "exposure": exposure,
        "ps_b0_result": {"passed": True, "mismatch_by_arm": {"MAPR": 0, "DIRECT": 0}}, "bcrh_precheck_result": {"common_host_valid": True}, "checkpoint_artifact": checkpoint_artifact(config) if artifact is None else artifact, "ps_b0_artifact": ps_b0_artifact(config) if ps_artifact is None else ps_artifact,
    }


def test_exact_stage_seed_budget_and_master_derivation() -> None:
    assert subject.IMPLEMENTATION_READY is True and subject.IMPLEMENTATION_BLOCKER is None
    for config in configs():
        config.validate()
        first = subject.derive_seed_master(config); second = subject.derive_seed_master(config)
        assert first == second and len(first["master"]) == 32
        assert first["external_master_override"] is False
        assert config.namespace == f"{subject.RUN_REVISION}/{config.stage}/{config.seed}"
    invalid = (
        replace(configs()[0], seed=2026090102), replace(configs()[0], updates=7),
        subject.BExploreRunConfig(subject.PRIMARY_STAGE, subject.OPTIONAL_SEEDS[0], 64),
        subject.BExploreRunConfig(subject.OPTIONAL_STAGE, subject.OPTIONAL_SEEDS[0], 64),
        subject.BExploreRunConfig(subject.OPTIONAL_STAGE, subject.OPTIONAL_SEEDS[0], 64, "training_variance", "N7_ENDPOINT"),
    )
    for config in invalid:
        with pytest.raises(subject.BExploreContractError):
            config.validate()
    assert "external_master" not in inspect.signature(subject.run_b_explore_runtime).parameters
    assert len({config.namespace for config in configs()}) == 6
    debug = configs()[0]
    argv_contract = subject._exact_argv_contract(debug, preflight_receipt=Path("preflight.json"), scratch_root=Path("scratch"), durable_root=Path("durable") / subject.RUN_REVISION / debug.stage / str(debug.seed), publication_root=Path("publication"))
    assert argv_contract["schema"] == "VNFC_BPCR_BEXP_R01_EXECUTABLE_CLI_V1" and argv_contract["draft_only"] is False and argv_contract["executable"] is True and argv_contract["standalone_ps_b0_then_debug"] is False
    readiness = argv_contract["ps_b0_readiness"]; formal = argv_contract["formal"]
    assert readiness["argv"][:3] == ("{python}", "scripts/run_vnfc_bpcr_b_explore.py", "ps-b0-readiness")
    assert readiness["construction_only"] is True and readiness["non_result"] is True and readiness["formal_checkpoint_gate"] is False
    assert formal["argv"][:3] == ("{python}", "scripts/run_vnfc_bpcr_b_explore.py", "debug") and formal["posttraining_ps_same_invocation"] is True
    assert tuple(formal["argv"][index] for index in (3, 5, 7)) == ("--stage", "--seed", "--updates")


def test_cli_import_has_no_output_or_files_and_bad_debug_rejects_before_roots(tmp_path: Path) -> None:
    imported = subprocess.run([sys.executable, "-c", "import scripts.run_vnfc_bpcr_b_explore"], cwd=Path.cwd(), capture_output=True, text=True, check=False)
    assert imported.returncode == 0 and imported.stdout == "" and imported.stderr == ""
    scratch = tmp_path / "scratch"; durable = tmp_path / "durable"; publication = tmp_path / "publication"; missing = tmp_path / "missing.json"
    rejected = subprocess.run([sys.executable, "scripts/run_vnfc_bpcr_b_explore.py", "debug", "--stage", "WRONG", "--seed", str(subject.DEBUG_SEED), "--updates", "8", "--preflight-receipt", str(missing), "--scratch-root", str(scratch), "--durable-root", str(durable), "--publication-root", str(publication)], cwd=Path.cwd(), capture_output=True, text=True, check=False)
    assert rejected.returncode == 2 and "requires exactly" in rejected.stderr and not any(path.exists() for path in (scratch, durable, publication))


def test_cli_ps_b0_readiness_is_canonical_construction_only_non_result(tmp_path: Path) -> None:
    now = datetime.now(timezone.utc); value = receipt(captured_at=now.isoformat(), assessed_at=now.isoformat())
    path = tmp_path / "preflight.json"; path.write_text(json.dumps(value, sort_keys=True, separators=(",", ":")), "utf-8")
    completed = subprocess.run([sys.executable, "scripts/run_vnfc_bpcr_b_explore.py", "ps-b0-readiness", "--preflight-receipt", str(path)], cwd=Path.cwd(), capture_output=True, text=True, check=False, timeout=120)
    assert completed.returncode == 0, completed.stderr
    output = json.loads(completed.stdout)
    assert completed.stdout == json.dumps(output, sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n"
    assert output["schema"] == "VNFC_BPCR_BEXP_R01_PS_B0_READINESS_V1" and output["construction_only"] is True and output["non_result"] is True and output["scientific_result"] is False
    assert output["state_count"] == 18 and output["host_call_ledger"]["primary_only_host_calls"] == 24
    assert all(value is False for value in output["forbidden_effects_observed"].values())
    assert {item.name for item in tmp_path.iterdir()} == {"preflight.json"}


def test_load_only_resolver_is_pure_filesystem_unique_missing_and_ambiguous(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    from experiments.candidates.variable_n_fleet_churn_b_explore import native_backend as b_native
    monkeypatch.setattr(b_native.subprocess, "run", lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("subprocess forbidden")))
    program = tmp_path / "pf"; cache = tmp_path / "cache"
    def add_compiler(version: str, payload: bytes) -> Path:
        path = program / "Microsoft Visual Studio" / "2022" / version / "VC" / "Tools" / "MSVC" / version / "bin" / "Hostx64" / "x64" / "cl.exe"; path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(payload); return path
    def add_pair(compiler: Path) -> None:
        sha = hashlib.sha256(compiler.read_bytes()).hexdigest(); rkey = b_native._r09_key_for_compiler_sha(sha); skey = b_native._shadow_key_for_compiler_sha(b_native._source_identity(), sha)
        primary = cache / "hmasd_vnfc_bpcr_r09_native" / rkey / "bpcr_backend.dll"; shadow = cache / "hmasd_vnfc_b_tick_native" / skey / "vnfc_b_tick_telemetry.dll"; primary.parent.mkdir(parents=True); shadow.parent.mkdir(parents=True); primary.write_bytes(b"primary"); shadow.write_bytes(b"shadow")
    first = add_compiler("BuildTools", b"compiler-one")
    with pytest.raises(b_native.NativeTelemetryError, match="found 0"): b_native.resolve_prebuilt_load_only_binding(program_files_roots=(program,), cache_root=cache)
    add_pair(first); binding = b_native.resolve_prebuilt_load_only_binding(program_files_roots=(program,), cache_root=cache)
    assert binding["compiler_sha256"] == hashlib.sha256(first.read_bytes()).hexdigest() and Path(binding["primary_artifact_path"]).is_file() and Path(binding["shadow_artifact_path"]).is_file()
    second = add_compiler("Community", b"compiler-two"); add_pair(second)
    with pytest.raises(b_native.NativeTelemetryError, match="found 2"): b_native.resolve_prebuilt_load_only_binding(program_files_roots=(program,), cache_root=cache)


def test_cli_debug_stale_preflight_precedes_resolver_and_valid_mock_calls_once(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    stale = tmp_path / "stale.json"; stale.write_text(json.dumps(receipt(captured_at="2026-08-31T00:00:00Z")), "utf-8")
    calls = {"resolver": 0, "sink": 0, "runtime": 0}
    monkeypatch.setattr(subject, "_resolve_and_install_prebuilt_load_only_binding", lambda: calls.__setitem__("resolver", calls["resolver"] + 1))
    base = ["debug", "--stage", subject.DEBUG_STAGE, "--seed", str(subject.DEBUG_SEED), "--updates", "8", "--preflight-receipt", str(stale), "--scratch-root", str(tmp_path / "scratch"), "--durable-root", str(tmp_path / "durable"), "--publication-root", str(tmp_path / "publication")]
    assert subject.main(base) == 2 and calls == {"resolver": 0, "sink": 0, "runtime": 0} and not any((tmp_path / name).exists() for name in ("scratch", "durable", "publication"))
    fresh = tmp_path / "fresh.json"; now = datetime.now(timezone.utc); fresh.write_text(json.dumps(receipt(captured_at=now.isoformat(), assessed_at=now.isoformat())), "utf-8"); base[base.index(str(stale))] = str(fresh)
    monkeypatch.setattr(subject, "_resolve_and_install_prebuilt_load_only_binding", lambda: calls.__setitem__("resolver", calls["resolver"] + 1) or {"schema": "binding"})
    monkeypatch.setattr(subject, "_current_prebuilt_native_artifacts", lambda: {str((tmp_path / "p.dll").resolve()): "a" * 64, str((tmp_path / "s.dll").resolve()): "b" * 64})
    import experiments.candidates.variable_n_fleet_churn_b_explore.process_telemetry as process
    class Sink:
        def __init__(self, **kwargs: object): calls["sink"] += 1
    monkeypatch.setattr(process, "ProcessTreeTelemetrySink", Sink)
    monkeypatch.setattr(subject, "run_b_explore_runtime", lambda *args, **kwargs: calls.__setitem__("runtime", calls["runtime"] + 1) or {"schema": "mock-success"})
    assert subject.main(base) == 0 and calls == {"resolver": 1, "sink": 1, "runtime": 1}
    assert json.loads(capsys.readouterr().out.splitlines()[-1]) == {"schema": "mock-success"}


def test_load_only_binding_survives_original_toolchain_and_subprocess_traps() -> None:
    code = """from experiments.candidates.variable_n_fleet_churn_b_explore import native_backend as b\nfrom experiments.candidates.variable_n_fleet_churn_bpcr_r09 import native_backend as r\ndef boom(*a,**k): raise AssertionError('forbidden original discovery/build')\nr.native_toolchain_identity=boom\nr.native_build_key=boom\nb.subprocess.run=boom\nx=b._install_prebuilt_load_only_binding(b.resolve_prebuilt_load_only_binding())\nr.require_cpp_batched_backend()\nb.require_b_native_telemetry()\nprint(x['schema'])\n"""
    completed = subprocess.run([sys.executable, "-c", code], cwd=Path.cwd(), capture_output=True, text=True, check=False, timeout=120)
    assert completed.returncode == 0, completed.stderr
    assert completed.stdout.strip() == "VNFC_BPCR_BEXP_R01_PREBUILT_LOAD_ONLY_BINDING_V1"


def test_private_load_only_installer_rejects_forged_facts_without_mutation(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    from experiments.candidates.variable_n_fleet_churn_b_explore import native_backend as b_native
    from experiments.candidates.variable_n_fleet_churn_bpcr_r09 import native_backend as r09_native
    assert "install_prebuilt_load_only_binding" not in b_native.__all__ and not hasattr(b_native, "install_prebuilt_load_only_binding")
    binding = b_native.resolve_prebuilt_load_only_binding()
    before = {"active": b_native.active_prebuilt_load_only_binding(), "b_key": b_native.native_build_key, "b_path": b_native._compiled_path, "r_key": r09_native.native_build_key, "r_path": r09_native._compiled_path, "r_cache": r09_native.require_cpp_batched_backend.cache_info(), "b_cache": b_native._load_b_native_telemetry.cache_info()}
    monkeypatch.setattr(b_native.ctypes, "CDLL", lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("DLL load forbidden during install validation")))
    mutations = (
        {"compiler_path": str(tmp_path / "missing" / "cl.exe")},
        {"compiler_sha256": "0" * 64},
        {"r09_build_key": "1" * 64},
        {"shadow_build_key": "2" * 64},
        {"source_identity": {**binding["source_identity"], "b_adapter_source_sha256": "3" * 64}},
        {"primary_artifact_path": binding["shadow_artifact_path"]},
        {"primary_artifact_sha256": "4" * 64},
    )
    for update in mutations:
        with pytest.raises(b_native.NativeTelemetryError): b_native._install_prebuilt_load_only_binding({**binding, **update})
        assert b_native.active_prebuilt_load_only_binding() == before["active"]
        assert b_native.native_build_key is before["b_key"] and b_native._compiled_path is before["b_path"] and r09_native.native_build_key is before["r_key"] and r09_native._compiled_path is before["r_path"]
        assert r09_native.require_cpp_batched_backend.cache_info() == before["r_cache"] and b_native._load_b_native_telemetry.cache_info() == before["b_cache"]


def test_exact_counts_and_evaluation_allocations() -> None:
    debug = subject.expected_counts(configs()[0]); primary = subject.expected_counts(configs()[1])
    assert (debug["training_episodes_total"], debug["joint_transitions_total"], debug["optimizer_steps_total"], debug["evaluation_rollouts_total"]) == (256, 1536, 256, 112)
    assert (primary["training_episodes_total"], primary["joint_transitions_total"], primary["optimizer_steps_total"], primary["evaluation_rollouts_total"]) == (2048, 12288, 2048, 208)
    assert subject.sequence_counts()["maximum"] == {
        "training_episodes_total": 10496, "joint_transitions_total": 62976,
        "optimizer_steps_total": 10496, "evaluation_rollouts_total": 1152,
    }
    for config in configs():
        plan = subject.evaluation_plan(config)
        assert len(plan["learned"]) + len(plan["bcrh"]) == subject.expected_counts(config)["evaluation_rollouts_total"]
        assert all(row["include_candidate_records"] is False for row in plan["bcrh"])
        assert plan["n7_namespace_disjoint_from_training"] is True
        assert plan["required_relabel_mismatch_count"] == {"MAPR": 0, "DIRECT": 0}
    assert debug["ps_b0_state_comparisons_not_rollouts"] == 288


def valid_ps_b0() -> tuple[subject.PSB0Comparison, ...]:
    rows = []
    for n, zone, kind, presentation, checkpoint, arm in sorted(subject.ps_b0_expected_addresses(), key=str):
        rows.append(subject.PSB0Comparison(
            n, zone, kind, presentation, checkpoint, arm, True, True, True, True, True,
            (1, None, 3, None), (1, None, 3, None),
            kind == "diagnostic_null_tie", kind == "later_fixed_or_acquiring",
            kind == "diagnostic_null_tie", 2 if kind == "diagnostic_null_tie" else 0,
            kind == "diagnostic_null_tie",
        ))
    return tuple(rows)


def test_ps_b0_exact_cardinality_structure_and_relabel() -> None:
    assert len(subject.ps_b0_state_descriptors()) == 18
    assert len(subject.ps_b0_expected_addresses()) == 288
    result = subject.validate_ps_b0(valid_ps_b0())
    assert result == {"schema": "VNFC_BPCR_BEXP_R01_PS_B0_V1", "descriptors": 18, "presentations": 4, "comparisons": 288, "mismatch_by_arm": {"MAPR": 0, "DIRECT": 0}, "passed": True}
    bad = list(valid_ps_b0()); bad[0] = replace(bad[0], inverse_mapped_physical_command=(None, None, None, None))
    with pytest.raises(subject.BExploreContractError, match="inverse physical-command mismatch"):
        subject.validate_ps_b0(bad)


def bcrh_rows(valid: bool = True) -> tuple[subject.BCRHPrecheckRow, ...]:
    return tuple(subject.BCRHPrecheckRow(zone, obstruction, relay, True, True, valid, True, True, 10, False) for zone in subject.ZONES for obstruction in (False, True) for relay in (False, True))


def test_bcrh_corner_precheck_is_no_records_and_comparator_local() -> None:
    assert subject.validate_bcrh_precheck(bcrh_rows())["comparison_status"] == "IDENTIFIED"
    assert subject.validate_bcrh_precheck(bcrh_rows(False)) == {"comparison_status": "NONIDENTIFIED", "common_host_valid": True, "bcrh_identified": False}
    with pytest.raises(subject.BExploreContractError, match="no candidate records"):
        subject.validate_bcrh_precheck(tuple(replace(row, include_candidate_records=True) for row in bcrh_rows()))


def test_pretraining_readiness_is_hard_fenced_before_native_for_debug_and_primary(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(subject, "IMPLEMENTATION_READY", False)
    monkeypatch.setattr(subject, "IMPLEMENTATION_BLOCKER", "test hard fence")
    calls = []
    def native(**kwargs: object) -> dict[str, object]:
        calls.append(kwargs); return {"schema": "injected-native"}
    for config in (configs()[0], configs()[1]):
        with pytest.raises(subject.BExploreContractError, match="REPAIR_REQUIRED"):
            subject.assess_pretraining_readiness(config, preflight_receipt=receipt(), telemetry_sink=Sink(), now=NOW, source_identity_digest="a" * 64, native_admission=native, archived_debug_valid_claim_path=tmp_path / "must-not-read.json", archived_debug_scientific_root=tmp_path / "must-not-read-root")
    assert calls == [] and list(tmp_path.iterdir()) == []
    plan = subject._exact_readiness_plan(configs()[0])
    assert subject.IMPLEMENTATION_READY is False and plan["implementation_ready"] is False
    assert {row["condition"] for row in plan["readiness_conditions"]} == {"fresh_4gib_preflight", "implementation_ready", "source_bound_ps_b0_actual_path_adapter", "process_tree_telemetry_sink_api", "measured_external_process_telemetry", "paired_shadow_boundary_and_source_equivalence", "create_once_started_transaction", "archived_valid_debug_gate"}
    satisfied = {row["condition"] for row in plan["readiness_conditions"] if row["satisfied"]}
    assert satisfied == {"source_bound_ps_b0_actual_path_adapter", "process_tree_telemetry_sink_api", "archived_valid_debug_gate"}
    assert plan["repair_required"]["missing_adapter"] is None and "measured DEBUG" in plan["repair_required"]["remaining"]
    assert "no equal-logit state is claimed" in plan["repair_required"]["required_semantics"]
    assert plan["shadow_telemetry"]["delayed_import_module"] == "experiments.candidates.variable_n_fleet_churn_b_explore"
    assert plan["shadow_telemetry"]["apis"] == ("PairedPrimaryShadowBatch", "BNativeTelemetryBatch", "require_boundary_equivalence", "derive_recovery_telemetry")
    assert plan["shadow_telemetry"]["execution_seam"].startswith("PairedPrimaryShadowBatch only")
    assert "operation-resolved" in plan["shadow_telemetry"]["host_call_cost"]


def test_preflight_telemetry_and_shadow_fail_closed() -> None:
    with pytest.raises(subject.BExploreContractError, match="below 4 GiB"):
        subject.validate_preflight_receipt(receipt(effective_available_bytes=3 * 1024**3), now=NOW)
    with pytest.raises(subject.BExploreContractError, match="not fresh"):
        subject.validate_preflight_receipt(receipt(captured_at="2026-09-01T11:00:00Z"), now=NOW)
    sink = Sink(); sink.fields = tuple(set(sink.fields) - {"process_tree_peak_rss_bytes"})
    with pytest.raises(subject.BExploreContractError, match="lacks required"):
        subject.validate_telemetry_sink(sink)
    with pytest.raises(subject.BExploreContractError, match="unmeasured"):
        subject.validate_telemetry_payload(telemetry(process_tree_peak_rss_bytes=None))
    for field in ("parameter_count_by_arm", "forward_calls_by_arm", "backward_calls_by_arm", "flop_exposure_by_arm"):
        with pytest.raises(subject.BExploreContractError, match="exposure"):
            subject.validate_telemetry_payload(telemetry(**{field: {"MAPR": float("nan"), "DIRECT": 1}}))
    shadow = shadow_receipt(f"{configs()[0].namespace}/N7z1/final/MAPR")
    assert subject.validate_shadow_receipt(shadow)["status"] == "EQUIVALENT_PAIRED_BATCH_OBSERVED"
    drifted_pair = {**shadow["paired_receipt"], "source_post": {"drift": True}}
    with pytest.raises(subject.BExploreContractError, match="authority"):
        subject.validate_shadow_receipt({**shadow, "paired_receipt": drifted_pair})
    with pytest.raises(subject.BExploreContractError, match="authority"):
        subject.validate_shadow_receipt({**shadow, "shadow_influenced_actions": True})
    with pytest.raises(subject.BExploreContractError, match="not canonical"):
        subject.validate_shadow_receipt({**shadow, "batch_id": "batch-N"})
    with pytest.raises(subject.BExploreContractError, match="source/artifact"):
        subject.validate_shadow_receipt({**shadow, "paired_receipt": {**shadow["paired_receipt"], "source_pre": {}, "source_post": {}}})
    bad_boundary = list(shadow["paired_receipt"]["boundaries"]); bad_boundary[2] = {**bad_boundary[2], "shadow_full_output_digest": "0" * 64}
    with pytest.raises(subject.BExploreContractError, match="equivalence differs"):
        subject.validate_shadow_receipt({**shadow, "paired_receipt": {**shadow["paired_receipt"], "boundaries": tuple(bad_boundary)}})


def test_named_output_plan_is_create_once_and_legacy_serializer_is_absent(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(subject, "IMPLEMENTATION_READY", True)
    debug = configs()[0]
    source = {"mode": "current_checkout_actual_bytes", "digest": "a" * 64}
    plan = subject._serialize_readiness_plan_once(tmp_path, debug, preflight_receipt=receipt(), now=NOW, source_identity_provider=lambda: source)
    assert plan.name == "PLAN.json" and json.loads(plan.read_text("ascii"))["namespace"] == debug.namespace
    assert json.loads(plan.read_text("ascii"))["source_identity"] == source
    with pytest.raises(subject.BExploreContractError, match="already exists"):
        subject._serialize_readiness_plan_once(tmp_path, debug, preflight_receipt=receipt(), now=NOW, source_identity_provider=lambda: source)
    assert not hasattr(subject, "serialize_named_outcome_once")
    assert not list(tmp_path.rglob("RESULT.json")) and not list(tmp_path.rglob("OUTCOME_CLAIM.json"))


def test_debug_gate_internal_validator_rejects_shallow_or_drifted(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(subject, "IMPLEMENTATION_READY", True)
    debug = configs()[0]; subject._create_started_manifest_once(tmp_path, debug, source={"digest": "s" * 64}, memory=subject.validate_preflight_receipt(receipt(), now=NOW), now=NOW); artifact = durable_checkpoint_artifact(tmp_path, debug); ps_artifact = durable_ps_b0_artifact(tmp_path, debug); terminal = runtime_terminal(debug, artifact, ps_artifact)
    shallow = dict(terminal); shallow["training"] = {}
    with pytest.raises(subject.BExploreContractError, match="training arm payload"):
        subject.validate_runtime_terminal(debug, shallow)
    scientific_root = subject.named_output_directory(tmp_path, debug); claim_path, _ = durable_three_artifact_bundle(scientific_root, tmp_path / "publication", debug, terminal)
    source_digest = terminal["source_pre_digest"]
    gate = subject.build_debug_gate_receipt(claim_path, debug_scientific_root=scientific_root, source_identity_digest=source_digest, preflight_receipt=receipt(), now=NOW)
    assert gate["valid"] is True and gate["result_artifact"]["valid_claim_filename"] == "VALID_CLAIM.json"
    for forbidden_name in ("INCOMPLETE.json", "OUTCOME_CLAIM.json"):
        forbidden = scientific_root / forbidden_name; forbidden.write_text("{}", "ascii")
        with pytest.raises(subject.BExploreContractError, match="unresolved/incomplete artifact"):
            subject.build_debug_gate_receipt(claim_path, debug_scientific_root=scientific_root, source_identity_digest=source_digest, preflight_receipt=receipt(), now=NOW)
        forbidden.unlink()
    invalidator = claim_path.parent / "OBSERVER_INCOMPLETE.json"; invalidator.write_text("{}", "ascii")
    with pytest.raises(subject.BExploreContractError, match="three-artifact bundle"):
        subject.build_debug_gate_receipt(claim_path, debug_scientific_root=scientific_root, source_identity_digest=source_digest, preflight_receipt=receipt(), now=NOW)
    invalidator.unlink()
    (scientific_root / "CHECKPOINTS.bin").write_bytes(b"drift")
    with pytest.raises(subject.BExploreContractError, match="artifact inventory drifted"):
        subject.build_debug_gate_receipt(claim_path, debug_scientific_root=scientific_root, source_identity_digest=source_digest, preflight_receipt=receipt(), now=NOW)


def test_serialized_ps_b0_deep_semantic_mutations_are_rejected(tmp_path: Path) -> None:
    debug = configs()[0]; artifact = durable_ps_b0_artifact(tmp_path, debug)
    directory = subject.named_output_directory(tmp_path, debug)
    payload = json.loads((directory / "PS_B0.json").read_text("ascii")); rows = payload["comparisons"]
    assert subject._validate_serialized_ps_b0_rows(rows) == payload["summary"]
    mutations = []
    def duplicate_address(value: list[dict[str, object]]) -> None: value[1] = copy.deepcopy(value[0])
    mutations.append(duplicate_address)
    def structural(value: list[dict[str, object]]) -> None: value[0]["physical_support_equal"] = False
    mutations.append(structural)
    def equal_logit(value: list[dict[str, object]]) -> None: value[0]["equal_logit_claim"] = True
    mutations.append(equal_logit)
    def score(value: list[dict[str, object]]) -> None: value[0]["score_probability_difference_diagnostics"]["deterministic_decoder"]["maximum_absolute_probability_difference_binary64"] = float("nan").hex()
    mutations.append(score)
    def trace_binding(value: list[dict[str, object]]) -> None: value[0]["canonical_trace"]["tokens"][0]["candidates"][0]["probability_binary64"] = 0.5.hex()
    mutations.append(trace_binding)
    for mutate in mutations:
        changed = copy.deepcopy(rows); mutate(changed)
        with pytest.raises(subject.BExploreContractError): subject._validate_serialized_ps_b0_rows(changed)
    payload["summary"] = {**payload["summary"], "passed": False}
    summary_root = tmp_path / "summary"; summary_root.mkdir(); path = summary_root / "PS_B0.json"
    path.write_text(json.dumps(payload, sort_keys=True, separators=(",", ":")), "ascii")
    identity = {**artifact, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
    with pytest.raises(subject.BExploreContractError, match="summary differs"):
        subject._validate_ps_b0_artifact(summary_root, debug, identity)


def test_no_n7_tuning_no_c_imports_exact_sources_and_raw_lf() -> None:
    signature = set(inspect.signature(subject.run_b_explore_runtime).parameters)
    assert not signature.intersection(subject.FORBIDDEN_N7_CONTROL_SURFACES)
    assert not hasattr(subject, "exact_readiness_plan")
    assert not {"derive_seed_master", "_exact_readiness_plan", "build_shadow_receipt", "assess_posttraining_debug_gate", "validate_runtime_terminal", "_run_after_pretraining_readiness", "_serialize_checkpoint_bundle_once"}.intersection(subject.__all__)
    path = Path(subject.__file__); source = path.read_text("utf-8"); tree = ast.parse(source)
    imports = {alias.name for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom)) for alias in node.names}
    assert not any(token in name for name in imports for token in ("evaluation", "frontier", "inference", "branch_reducer"))
    forbidden = ("full_panel_plan", "execute_plan", "ExactPanelReducer", "run_cut_batch", "AtomicFrontier", "seal_complete")
    assert not any(name in source for name in forbidden)
    assert "NativeInteractiveBatch(" not in source and "BNativeTelemetryBatch(" not in source
    assert source.count("PairedPrimaryShadowBatch(") == 3
    assert "HELDOUT-N7-UNOPENED" in source and "fresh_relabel_each_learned_decision" in source
    assert not hasattr(subject, "serialize_named_outcome_once")
    assert "RESULT.json" not in inspect.getsource(subject.run_b_explore_runtime)
    assert "OUTCOME_CLAIM.json" not in inspect.getsource(subject.run_b_explore_runtime)
    subject._require_serial_no_child_runner()
    assert set(subject._ACTUAL_SOURCE_PATHS) == {
        "scripts/run_vnfc_bpcr_b_explore.py",
        "experiments/candidates/variable_n_fleet_churn_bpcr_r09/contracts.py",
        "experiments/candidates/variable_n_fleet_churn_bpcr_r09/empirical_contract.py",
        "experiments/candidates/variable_n_fleet_churn_bpcr_r09/empirical_training.py",
        "experiments/candidates/variable_n_fleet_churn_bpcr_r09/fixtures.py",
        "experiments/candidates/variable_n_fleet_churn_bpcr_r09/models.py",
        "experiments/candidates/variable_n_fleet_churn_bpcr_r09/native_backend.py",
        "experiments/candidates/variable_n_fleet_churn_bpcr_r09/numeric.py",
        "experiments/candidates/variable_n_fleet_churn_bpcr_r09/production.py",
        "experiments/candidates/variable_n_fleet_churn_bpcr_r09/rng.py",
        "experiments/candidates/variable_n_fleet_churn_bpcr_r09/services.py",
        "experiments/candidates/variable_n_fleet_churn_bpcr_r09/torch_models.py",
        "experiments/candidates/variable_n_fleet_churn_bpcr_r09/training.py",
        "experiments/candidates/variable_n_fleet_churn_bpcr_r09/native/bpcr_backend.cpp",
        "experiments/candidates/variable_n_fleet_churn_bpcr_r09/native/bpcr_checker.hpp",
        "experiments/candidates/variable_n_fleet_churn_bpcr_r09/native/bpcr_general.hpp",
        "experiments/candidates/variable_n_fleet_churn_b_explore/__init__.py",
        "experiments/candidates/variable_n_fleet_churn_b_explore/native_backend.py",
        "experiments/candidates/variable_n_fleet_churn_b_explore/process_telemetry.py",
        "experiments/candidates/variable_n_fleet_churn_b_explore/ps_b0.py",
        "experiments/candidates/variable_n_fleet_churn_b_explore/native/telemetry_backend.cpp",
        "docs/research/candidates/variable_n_fleet_churn/VNFC_UAV_BOUNDED_POST_CHURN_RECOVERY_SCIENCE_CARD.md",
        "docs/research/candidates/variable_n_fleet_churn/VNFC_TARGET_EXCLUSIVE_POST_CHURN_RECOVERY_SCIENCE_CARD.md",
    }
    for raw_path in (path, Path(__file__)):
        assert b"\r\n" not in raw_path.read_bytes()


def test_public_runtime_validates_preflight_then_fences_before_all_side_effects(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(subject, "IMPLEMENTATION_READY", False)
    monkeypatch.setattr(subject, "IMPLEMENTATION_BLOCKER", "test hard fence")
    samples = iter(({"files": (1,), "native": 1}, {"files": (2,), "native": 1}))
    monkeypatch.setattr(subject, "_source_identity", lambda: next(samples))
    fence = subject._SourceFence.capture()
    with pytest.raises(subject.BExploreContractError, match="identity drifted"):
        fence.close()
    events = []; original = subject.validate_preflight_receipt
    def checked(value: dict[str, object], *, now: datetime) -> dict[str, object]:
        events.append("preflight"); return original(value, now=now)
    monkeypatch.setattr(subject, "validate_preflight_receipt", checked)
    monkeypatch.setattr(subject.torch, "get_num_threads", lambda: events.append("threads") or 7)
    monkeypatch.setattr(subject, "_SourceFence", type("Fence", (), {"capture": classmethod(lambda cls: events.append("source"))}))
    def native(**kwargs: object) -> dict[str, object]: events.append("native"); return {}
    for config in (configs()[0], configs()[1]):
        scratch, durable, publication = invocation_roots(tmp_path / config.stage, config)
        with pytest.raises(subject.BExploreContractError, match="REPAIR_REQUIRED"):
            subject.run_b_explore_runtime(config, preflight_receipt=receipt(), telemetry_sink=Sink(), now=NOW, scratch_root=scratch, durable_root=durable, publication_root=publication, archived_debug_valid_claim_path=tmp_path / "must-not-read", archived_debug_scientific_root=tmp_path / "must-not-read-root")
    assert events == ["preflight", "preflight"] and list(tmp_path.iterdir()) == []


def test_debug_runtime_wiring_trains_before_gate_and_freezes_before_any_evaluation(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    events = []
    class Fence:
        identity = {"source": "fixed"}
        @classmethod
        def capture(cls) -> "Fence":
            events.append("source-pre"); return cls()
        def close(self) -> None:
            events.append("source-post")
    monkeypatch.setattr(subject, "_SourceFence", Fence)
    learners = {"models": {"MAPR": object(), "DIRECT": object()}, "optimizers": {"MAPR": object(), "DIRECT": object()}}
    monkeypatch.setattr(subject, "_initialize_learners", lambda *args, **kwargs: events.append("initialize") or learners)
    training = {arm: {"updates": 8, "episodes": 128, "joint_transitions": 768, "optimizer_steps": 128, "updates_telemetry": ()} for arm in subject.ARMS}
    monkeypatch.setattr(subject, "_train_learners", lambda *args, **kwargs: events.append("train-N3-N5") or training)
    monkeypatch.setattr(subject, "clone_checkpoint", lambda model, label: events.append(f"checkpoint-{label}") or {"label": label, "state": {"p": torch.zeros(1)}, "sha256": label, "storage_disjoint": True})
    monkeypatch.setattr(subject, "validate_checkpoint_pair", lambda *args, **kwargs: None)
    monkeypatch.setattr(subject, "_serialize_checkpoint_bundle_once", lambda *args, **kwargs: events.append("persist-checkpoints") or checkpoint_artifact(configs()[0]))
    monkeypatch.setattr(subject, "_serialize_ps_b0_artifact_once", lambda *args, **kwargs: events.append("persist-ps-b0") or ps_b0_artifact(configs()[0]))
    gate = {"runtime_ready": True, "ps_b0_result": {"passed": True}, "bcrh_result": {"common_host_valid": True}}
    monkeypatch.setattr(subject, "assess_posttraining_debug_gate", lambda *args, **kwargs: events.append("posttrain-PS-B0-BCRH") or gate)
    token = subject._HeldoutFreezeToken(configs()[0].namespace, "frozen")
    monkeypatch.setattr(subject, "_freeze_before_n7", lambda *args, **kwargs: events.append("freeze-before-N7") or token)
    evaluation = {"learned": (), "bcrh": (), "rollouts": 112, "relabel_mismatch_count": {"MAPR": 0, "DIRECT": 0}}
    monkeypatch.setattr(subject, "_execute_evaluation", lambda *args, **kwargs: events.append("evaluate-including-N7") or evaluation)
    monkeypatch.setattr(subject, "_runtime_terminal", lambda *args, **kwargs: events.append("terminal") or {"schema": "fake-terminal"})
    monkeypatch.setattr(subject, "_serialize_result_body_once", lambda *args, **kwargs: events.append("persist-result-body") or {"schema": "fake-result-body"})
    class Monitor:
        def stage(self, name: str) -> object:
            class Stage:
                def __enter__(self) -> None: events.append(f"stage-{name}-start")
                def __exit__(self, *args: object) -> None: events.append(f"stage-{name}-end")
            return Stage()
    fence = Fence.capture()
    result = subject._run_after_pretraining_readiness(configs()[0], now=NOW, fence=fence, source_digest="a" * 64, diagnostic_state_adapter=object(), archived_debug_gate_receipt=None, output_root=tmp_path, telemetry_sink=Monitor())
    assert result == {"runtime_terminal": {"schema": "fake-terminal"}, "result_body": {"schema": "fake-result-body"}}
    assert events.index("train-N3-N5") < events.index("posttrain-PS-B0-BCRH") < events.index("freeze-before-N7") < events.index("evaluate-including-N7")
    assert [row for row in events if row.startswith("stage-")] == ["stage-training-start", "stage-training-end", "stage-evaluation-start", "stage-evaluation-end", "stage-serialization-start", "stage-serialization-end"]


def test_public_serializers_and_debug_gate_hard_fence_before_files(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(subject, "IMPLEMENTATION_READY", False)
    monkeypatch.setattr(subject, "IMPLEMENTATION_BLOCKER", "test hard fence")
    creates = []
    monkeypatch.setattr(subject, "_create_once_json", lambda *args, **kwargs: creates.append(args) or tmp_path / "forbidden")
    debug = configs()[0]
    calls = (
        lambda: subject._serialize_readiness_plan_once(tmp_path, debug, preflight_receipt=receipt(), now=NOW),
        lambda: subject.build_debug_gate_receipt(tmp_path / "must-not-be-read.json", debug_scientific_root=tmp_path / "must-not-be-read-root", source_identity_digest="a" * 64, preflight_receipt=receipt(), now=NOW),
    )
    for call in calls:
        with pytest.raises(subject.BExploreContractError, match="REPAIR_REQUIRED"):
            call()
    assert creates == [] and list(tmp_path.iterdir()) == []


def test_post_start_failures_have_one_quarantined_terminal_and_no_orphan(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(subject, "IMPLEMENTATION_READY", True)
    monkeypatch.setattr(subject, "_source_bytes_identity", lambda: {"mode": "test", "files": (), "digest": "s" * 64})
    class Fence:
        identity = {"mode": "test-full", "digest": "f" * 64}
        @classmethod
        def capture(cls) -> "Fence": return cls()
        def close(self) -> None: pass
    monkeypatch.setattr(subject, "_SourceFence", Fence)
    monkeypatch.setattr(subject, "assess_pretraining_readiness", lambda *args, **kwargs: {"pretraining_ready": True, "debug_gate_receipt": None})
    monkeypatch.setattr(subject, "_load_source_bound_diagnostic_adapter", lambda: object())
    monkeypatch.setattr(subject, "_validate_exact_storage_contract_binding", lambda *args, **kwargs: None)
    monkeypatch.setattr(subject, "_require_process_tree_telemetry_sink", lambda *args, **kwargs: None)
    monkeypatch.setattr(subject, "_require_prebuilt_serial_native_contract", lambda *args, **kwargs: None)
    monkeypatch.setattr(subject, "_require_serial_no_child_runner", lambda: None)
    class Monitor(Sink):
        def __init__(self, scratch: Path, durable: Path): self.scratch_root = scratch; self.durable_root = durable
        def start(self) -> "Monitor": return self
        def stage(self, name: str) -> object: return nullcontext()
        def finish_incomplete(self, **kwargs: object) -> dict[str, object]: self.incomplete_finish = kwargs; return {"attempt_disposition": "INCOMPLETE"}
        def verify_storage_seal(self) -> dict[str, object]: return {"valid": True}
        def publish_observer_bundle(self, root: Path, **kwargs: object) -> dict[str, object]: self.incomplete_publication = kwargs; return {"claim_disposition": "INCOMPLETE"}
        def verify_observer_publication(self) -> dict[str, object]: return {"valid": True}
        def abort(self) -> None: pass
    for stage in ("native", "rng", "model", "checkpoint"):
        root = tmp_path / stage
        scratch, durable, publication = invocation_roots(root, configs()[0])
        def fail_after_started(*args: object, **kwargs: object) -> dict[str, object]:
            state = kwargs["execution_state"]
            if stage in ("rng", "model", "checkpoint"): state["rng_created"] = True
            if stage in ("model", "checkpoint"): state["model_created"] = True
            if stage == "checkpoint":
                model = torch.nn.Linear(2, 1, dtype=torch.float64)
                state["checkpoint_created"] = True; state["checkpoints"] = {"MAPR": {"initial": subject.clone_checkpoint(model, "initial")}}
            raise RuntimeError(f"fail-{stage}")
        monkeypatch.setattr(subject, "_run_after_pretraining_readiness", fail_after_started)
        with pytest.raises(RuntimeError, match=f"fail-{stage}"):
            subject.run_b_explore_runtime(configs()[0], preflight_receipt=receipt(), telemetry_sink=Monitor(scratch, durable), now=NOW, scratch_root=scratch, durable_root=durable, publication_root=publication)
        directory = durable; names = {path.name for path in directory.iterdir()}
        assert {"STARTED.json", "INCOMPLETE.json"} <= names and not {"RESULT.json", "OUTCOME_CLAIM.json"}.intersection(names)
        incomplete = json.loads((directory / "INCOMPLETE.json").read_text("ascii"))
        assert incomplete["status"] == "INCOMPLETE" and incomplete["scientific_result"] is False and incomplete["quarantine_only"] is True
        assert incomplete["resume_allowed"] is False and incomplete["evaluation_allowed"] is False and incomplete["publication_allowed"] is False
        assert incomplete["execution_flags"]["native_phase_entered"] is True
        if stage == "checkpoint":
            assert {"QUARANTINE_CHECKPOINTS.bin", "QUARANTINE_CHECKPOINTS_MANIFEST.json"} <= names
            assert any(row["filename"] == "QUARANTINE_CHECKPOINTS.bin" for row in incomplete["partial_artifacts"])
        else:
            assert not any(name.startswith("QUARANTINE_CHECKPOINTS") for name in names)


def test_future_runtime_orders_monitor_stages_finish_binding_then_result(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(subject, "IMPLEMENTATION_READY", True); events = []; terminal = runtime_terminal(configs()[0]); body = {"schema": "VNFC_BPCR_BEXP_R01_RESULT_BODY_IDENTITY_V1", "namespace": configs()[0].namespace, "filename": "RESULT_BODY.json", "sha256": "b" * 64, "size_bytes": 7, "runtime_terminal_sha256": subject._canonical_digest(terminal)}
    scratch, durable, publication = invocation_roots(tmp_path, configs()[0])
    monkeypatch.setattr(subject, "_require_process_tree_telemetry_sink", lambda *args, **kwargs: None)
    monkeypatch.setattr(subject, "_source_bytes_identity", lambda: {"mode": "test", "files": (), "digest": "s" * 64})
    class Fence:
        identity = {"mode": "test-full", "digest": "f" * 64}
        @classmethod
        def capture(cls) -> "Fence": events.append("source-native"); return cls()
        def close(self) -> None: pass
    monkeypatch.setattr(subject, "_SourceFence", Fence)
    monkeypatch.setattr(subject, "assess_pretraining_readiness", lambda *args, **kwargs: {"pretraining_ready": True, "debug_gate_receipt": None})
    monkeypatch.setattr(subject, "_load_source_bound_diagnostic_adapter", lambda: object())
    monkeypatch.setattr(subject, "_validate_exact_storage_contract_binding", lambda *args, **kwargs: None)
    monkeypatch.setattr(subject, "_require_prebuilt_serial_native_contract", lambda *args, **kwargs: None)
    monkeypatch.setattr(subject, "_require_serial_no_child_runner", lambda: None)
    class Monitor(Sink):
        scratch_root = scratch; durable_root = durable
        def start(self) -> "Monitor": events.append("monitor-start"); return self
        def stage(self, name: str) -> object:
            class Stage:
                def __enter__(self) -> None: events.append(f"{name}-start")
                def __exit__(self, *args: object) -> None: events.append(f"{name}-end")
            return Stage()
        def finish(self, **kwargs: object) -> dict[str, object]: events.append("monitor-finish"); self.finish_kwargs = kwargs; return bound_telemetry(terminal)
        def publish_observer_bundle(self, root: Path, **kwargs: object) -> dict[str, object]:
            events.append("observer-publish"); self.publication = (Path(root), dict(kwargs)); return {"valid": True}
        def verify_storage_seal(self) -> dict[str, object]: events.append("verify-scientific"); return {"valid": True}
        def verify_observer_publication(self) -> dict[str, object]: events.append("verify-observer"); return {"valid": True}
        def emit(self, payload: object) -> None: events.append("monitor-emit")
        def abort(self) -> None: events.append("monitor-abort")
    monitor = Monitor()
    def after(*args: object, **kwargs: object) -> dict[str, object]:
        sink = kwargs["telemetry_sink"]
        for name in ("training", "evaluation", "serialization"):
            with sink.stage(name): pass
        return {"runtime_terminal": terminal, "result_body": body}
    monkeypatch.setattr(subject, "_run_after_pretraining_readiness", after)
    result = subject.run_b_explore_runtime(configs()[0], preflight_receipt=receipt(), telemetry_sink=monitor, now=NOW, scratch_root=scratch, durable_root=durable, publication_root=publication)
    assert result["schema"] == "VNFC_BPCR_BEXP_R01_EXECUTION_RESULT_V1"
    assert events == ["monitor-start", "source_binding-start", "source-native", "source_binding-end", "training-start", "training-end", "evaluation-start", "evaluation-end", "serialization-start", "serialization-end", "monitor-finish", "verify-scientific", "observer-publish", "verify-observer", "monitor-emit"]
    assert monitor.finish_kwargs["host_call_ledger"] == {"primary_host_calls": terminal["host_call_ledger"]["primary_total"], "shadow_host_calls": terminal["host_call_ledger"]["shadow_total"]}
    assert monitor.finish_kwargs["host_call_ledger"]["primary_host_calls"] == terminal["host_call_ledger"]["paired_primary_shadow"]["primary_total"] + 24
    assert monitor.finish_kwargs["scientific_counters"]["native_integrated_ticks"] == terminal["host_call_ledger"]["paired_primary_shadow"]["operations"]["paired_successful_step"] * 8 * 20
    assert terminal["host_call_ledger"]["paired_primary_shadow"]["operations"]["primary_sensitivity"] == 4
    assert terminal["host_call_ledger"]["paired_primary_shadow"]["operations"]["primary_bcrh"] == 12
    assert monitor.publication == (publication, {"namespace": configs()[0].namespace, "scientific_body_relative_path": "RESULT_BODY.json", "publication_root_is_new_namespace": True})


@pytest.mark.parametrize("failure_stage", ("publish", "verify", "emit"))
def test_post_seal_observer_failures_create_only_invalidate_publication(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, failure_stage: str) -> None:
    monkeypatch.setattr(subject, "IMPLEMENTATION_READY", True)
    config = configs()[0]; terminal = runtime_terminal(config)
    body = {"schema": "VNFC_BPCR_BEXP_R01_RESULT_BODY_IDENTITY_V1", "namespace": config.namespace, "filename": "RESULT_BODY.json", "sha256": "b" * 64, "size_bytes": 7, "runtime_terminal_sha256": subject._canonical_digest(terminal)}
    scratch, durable, publication = invocation_roots(tmp_path / failure_stage, config)
    monkeypatch.setattr(subject, "_require_process_tree_telemetry_sink", lambda *args, **kwargs: None)
    monkeypatch.setattr(subject, "_require_prebuilt_serial_native_contract", lambda *args, **kwargs: None)
    monkeypatch.setattr(subject, "_require_serial_no_child_runner", lambda: None)
    monkeypatch.setattr(subject, "_source_bytes_identity", lambda: {"mode": "test", "files": (), "digest": "s" * 64})
    class Fence:
        identity = {"mode": "test-full", "digest": "f" * 64}
        @classmethod
        def capture(cls) -> "Fence": return cls()
        def close(self) -> None: pass
    monkeypatch.setattr(subject, "_SourceFence", Fence)
    monkeypatch.setattr(subject, "assess_pretraining_readiness", lambda *args, **kwargs: {"pretraining_ready": True, "debug_gate_receipt": None})
    monkeypatch.setattr(subject, "_load_source_bound_diagnostic_adapter", lambda: object())
    monkeypatch.setattr(subject, "_validate_exact_storage_contract_binding", lambda *args, **kwargs: None)
    class Monitor(Sink):
        scratch_root = scratch; durable_root = durable
        def start(self) -> "Monitor": return self
        def stage(self, name: str) -> object: return nullcontext()
        def finish(self, **kwargs: object) -> dict[str, object]: return bound_telemetry(terminal)
        def verify_storage_seal(self) -> dict[str, object]: return {"storage_high_water_disposition": "EXACT_R01_MONOTONIC_CREATE_ONLY", "durable_artifact_inventory": ({"relative_path": "RESULT_BODY.json", "size_bytes": 7, "sha256": "b" * 64},), "valid": True}
        def publish_observer_bundle(self, root: Path, **kwargs: object) -> dict[str, object]:
            if failure_stage == "publish": raise RuntimeError("observer-publish-failure")
            Path(root).mkdir(parents=True); (Path(root) / "TELEMETRY_TERMINAL.json").write_bytes(b"partial-telemetry"); (Path(root) / "VALID_CLAIM.json").write_bytes(b"partial-claim")
            return {"valid": True}
        def verify_observer_publication(self) -> dict[str, object]:
            if failure_stage == "verify": raise RuntimeError("observer-verify-failure")
            return {"valid": True}
        def emit(self, payload: object) -> None:
            if failure_stage == "emit": raise RuntimeError("observer-emit-failure")
        def abort(self) -> None: pass
    monkeypatch.setattr(subject, "_run_after_pretraining_readiness", lambda *args, **kwargs: {"runtime_terminal": terminal, "result_body": body})
    with pytest.raises(RuntimeError, match=f"observer-{failure_stage}-failure"):
        subject.run_b_explore_runtime(config, preflight_receipt=receipt(), telemetry_sink=Monitor(), now=NOW, scratch_root=scratch, durable_root=durable, publication_root=publication)
    scientific_files = tuple(sorted(path.name for path in durable.iterdir()))
    marker_path = publication / "OBSERVER_INCOMPLETE.json"
    marker = json.loads(marker_path.read_text("ascii"))
    assert marker["failure_stage"] == failure_stage and marker["scientific_body"] == body
    assert marker["valid_claim_usable"] is False and marker["observer_emit_completed"] is False and marker["scientific_result"] is False
    assert marker["scientific_storage_seal_sha256"] == subject._canonical_digest(marker["scientific_storage_seal"])
    assert scientific_files == ("STARTED.json",) and not {"INCOMPLETE.json", "OUTCOME_CLAIM.json"}.intersection(scientific_files)
    if failure_stage == "publish":
        assert {path.name for path in publication.iterdir()} == {"OBSERVER_INCOMPLETE.json"}
    else:
        assert {path.name for path in publication.iterdir()} == {"TELEMETRY_TERMINAL.json", "VALID_CLAIM.json", "OBSERVER_INCOMPLETE.json"}


def test_runner_create_once_writes_use_active_exact_storage_recorder(tmp_path: Path) -> None:
    durable = tmp_path / "durable"; durable.mkdir(); observed = []
    class Recorder:
        durable_root = durable
        def mark_incomplete(self, reason: str) -> None: self.reason = reason
        def observe_create_once(self, relative: Path) -> object:
            class Observation:
                def __enter__(self) -> Path: observed.append(str(relative).replace("\\", "/")); return durable / relative
                def __exit__(self, *args: object) -> None: pass
            return Observation()
        def observe_incomplete_create_once(self, relative: Path, *, reason: str) -> object: return self.observe_create_once(relative)
    token = subject._ACTIVE_DURABLE_RECORDER.set(Recorder())
    try:
        subject._create_once_json(durable / "STARTED.json", {"status": "started"})
        subject._create_once_bytes(durable / "CHECKPOINTS.bin", b"checkpoint")
    finally:
        subject._ACTIVE_DURABLE_RECORDER.reset(token)
    assert observed == ["STARTED.json", "CHECKPOINTS.bin"]
    assert (durable / "STARTED.json").is_file() and (durable / "CHECKPOINTS.bin").read_bytes() == b"checkpoint"


def test_checkpoint_manifest_failure_preserves_registered_bundle_then_quarantines(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    config = configs()[0]; durable = subject.named_output_directory(tmp_path, config); durable.mkdir(parents=True); observed = []
    class Recorder:
        durable_root = durable
        def mark_incomplete(self, reason: str) -> None: self.reason = reason
        def observe_create_once(self, relative: Path) -> object:
            class Observation:
                def __enter__(self) -> Path: observed.append(str(relative).replace("\\", "/")); return durable / relative
                def __exit__(self, *args: object) -> None: pass
            return Observation()
        def observe_incomplete_create_once(self, relative: Path, *, reason: str) -> object: return self.observe_create_once(relative)
    checkpoints = {}
    for arm in subject.ARMS:
        model = torch.nn.Linear(2, 1, dtype=torch.float64)
        checkpoints[arm] = {label: subject.clone_checkpoint(model, label) for label in subject.CHECKPOINTS}
    original_json = subject._create_once_json
    def fail_manifest(path: Path, payload: dict[str, object]) -> Path:
        if Path(path).name == "CHECKPOINTS_MANIFEST.json": raise RuntimeError("manifest-construction-failure")
        return original_json(path, payload)
    token = subject._ACTIVE_DURABLE_RECORDER.set(Recorder())
    try:
        monkeypatch.setattr(subject, "_create_once_json", fail_manifest)
        with pytest.raises(RuntimeError, match="manifest-construction-failure"):
            subject._serialize_checkpoint_bundle_once(tmp_path, config, checkpoints)
        assert (durable / "CHECKPOINTS.bin").is_file() and "CHECKPOINTS.bin" in observed
        monkeypatch.setattr(subject, "_create_once_json", original_json)
        subject._quarantine_incomplete_once(tmp_path, config, source={"mode": "test"}, execution_state={"rng_created": True, "model_created": True, "native_phase_entered": True, "checkpoint_created": True}, error=RuntimeError("manifest-construction-failure"))
    finally:
        subject._ACTIVE_DURABLE_RECORDER.reset(token)
    assert {"CHECKPOINTS.bin", "INCOMPLETE.json"} <= {path.name for path in durable.iterdir()} and not (durable / "OUTCOME_CLAIM.json").exists()
    assert not list(durable.glob("RESULT*.json")) and ".unlink(" not in Path(subject.__file__).read_text("utf-8")


def test_real_recorder_write_body_failure_seals_canonical_incomplete_bundle(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    from experiments.candidates.variable_n_fleet_churn_b_explore.process_telemetry import ExactStorageContract, ProcessSample, ProcessTreeTelemetrySink
    monkeypatch.setattr(subject, "IMPLEMENTATION_READY", True)
    config = configs()[0]; scratch, durable, publication = invocation_roots(tmp_path, config)
    scratch.mkdir(parents=True); durable.mkdir(parents=True); publication.mkdir(parents=True)
    native = tmp_path / "frozen-native.dll"; native.write_bytes(b"native")
    contract = ExactStorageContract(frozen_native_artifacts={str(native.resolve()): hashlib.sha256(native.read_bytes()).hexdigest()}, scratch_not_shared_with_children_or_loaders=True, durable_root_is_new_namespace=True, durable_writes_use_create_once_recorder_only=True, serial_no_child_processes=True, source_stage_loads_frozen_native_without_build=True)
    samples = 0
    def sampler(_tracked: object = None) -> tuple[ProcessSample, ...]:
        nonlocal samples; samples += 1; return (ProcessSample(10, 100, 1024 + samples, float(samples), samples, samples, 0, 1),)
    sink = ProcessTreeTelemetrySink(preflight_receipt=receipt(), scratch_root=scratch, durable_root=durable, now=NOW, sample_interval_seconds=3600.0, sampler=sampler, logical_processor_count=2, test_mode=True, exact_storage_contract=contract)
    monkeypatch.setattr(subject, "_require_process_tree_telemetry_sink", lambda *args, **kwargs: None)
    monkeypatch.setattr(subject, "_require_prebuilt_serial_native_contract", lambda *args, **kwargs: None)
    monkeypatch.setattr(subject, "_require_serial_no_child_runner", lambda: None)
    monkeypatch.setattr(subject, "_source_bytes_identity", lambda: {"mode": "test", "files": (), "digest": "s" * 64})
    class Fence:
        identity = {"mode": "test-full", "digest": "f" * 64}
        @classmethod
        def capture(cls) -> "Fence": return cls()
        def close(self) -> None: pass
    monkeypatch.setattr(subject, "_SourceFence", Fence)
    monkeypatch.setattr(subject, "assess_pretraining_readiness", lambda *args, **kwargs: {"pretraining_ready": True, "debug_gate_receipt": None})
    monkeypatch.setattr(subject, "_load_source_bound_diagnostic_adapter", lambda: object())
    monkeypatch.setattr(subject, "_validate_exact_storage_contract_binding", lambda *args, **kwargs: None)
    checkpoints = {}
    for arm in subject.ARMS:
        model = torch.nn.Linear(2, 1, dtype=torch.float64); checkpoints[arm] = {label: subject.clone_checkpoint(model, label) for label in subject.CHECKPOINTS}
    original_json = subject._create_once_json
    def write_body_failure(path: Path, payload: dict[str, object]) -> Path:
        if Path(path).name != "CHECKPOINTS_MANIFEST.json": return original_json(path, payload)
        recorder = subject._ACTIVE_DURABLE_RECORDER.get(); relative = Path(path).resolve().relative_to(Path(recorder.durable_root).resolve())
        with recorder.observe_create_once(relative) as authorized:
            Path(authorized).write_bytes(b"partial-manifest")
            raise OSError("real-write-body-failure")
    monkeypatch.setattr(subject, "_create_once_json", write_body_failure)
    def fail_after(*args: object, **kwargs: object) -> dict[str, object]:
        monitor = kwargs["telemetry_sink"]
        with monitor.stage("training"): pass
        with monitor.stage("evaluation"): pass
        with monitor.stage("serialization"): subject._serialize_checkpoint_bundle_once(kwargs["output_root"], config, checkpoints)
        raise AssertionError("unreachable")
    monkeypatch.setattr(subject, "_run_after_pretraining_readiness", fail_after)
    with pytest.raises(OSError, match="real-write-body-failure"):
        subject.run_b_explore_runtime(config, preflight_receipt=receipt(), telemetry_sink=sink, now=NOW, scratch_root=scratch, durable_root=durable, publication_root=publication)
    assert {"STARTED.json", "CHECKPOINTS.bin", "CHECKPOINTS_MANIFEST.json", "INCOMPLETE.json"} <= {path.name for path in durable.iterdir()}
    assert not {"RESULT_BODY.json", "OUTCOME_CLAIM.json"}.intersection(path.name for path in durable.iterdir())
    assert {path.name for path in publication.iterdir()} == {"TELEMETRY_TERMINAL.json", "INCOMPLETE_CLAIM.json"}
    telemetry_doc = json.loads((publication / "TELEMETRY_TERMINAL.json").read_text("utf-8")); claim = json.loads((publication / "INCOMPLETE_CLAIM.json").read_text("utf-8"))
    assert telemetry_doc["telemetry"]["attempt_disposition"] == "INCOMPLETE" and telemetry_doc["telemetry"]["scientific_result_valid"] is False
    assert claim["schema"] == "VNFC_BPCR_BEXP_R01_INCOMPLETE_CLAIM_V1" and not (publication / "VALID_CLAIM.json").exists()


def test_deep_runtime_mutations_are_rejected() -> None:
    config = configs()[0]; base = runtime_terminal(config)
    mutations = []
    def recovery(value: dict[str, object]) -> None: value["shadow_receipts"][0]["episode_recovery"][0]["raw_tick_rows"][1]["post_loss_second"] = 0
    mutations.append(recovery)
    def ledger(value: dict[str, object]) -> None: value["host_call_ledger"]["primary_total"] += 1
    mutations.append(ledger)
    def sensitivity(value: dict[str, object]) -> None: next(row for row in value["evaluation"]["learned"] if row["cell"].startswith("N7"))["action_sensitivity"][0]["world"] = 7
    mutations.append(sensitivity)
    def direct(value: dict[str, object]) -> None: next(row for row in value["evaluation"]["learned"] if row["arm"] == "DIRECT")["direct_residual_activity"][0]["total_variation"] = float("nan")
    mutations.append(direct)
    def bcrh(value: dict[str, object]) -> None: value["evaluation"]["bcrh"][0]["checker_rows"][0]["candidate_count"] = 0
    mutations.append(bcrh)
    def readout(value: dict[str, object]) -> None: value["exploratory_readout"]["individual_world_seed"][0]["J_ext"] += .1
    mutations.append(readout)
    for mutate in mutations:
        terminal = copy.deepcopy(base); mutate(terminal)
        with pytest.raises(subject.BExploreContractError):
            subject.validate_runtime_terminal(config, terminal)


@pytest.mark.parametrize("swap_kind", ("training_training", "evaluation_training", "evaluation_evaluation"))
def test_group_local_receipt_swaps_are_rejected_even_with_global_set_preserved(swap_kind: str) -> None:
    config = configs()[0]; terminal = runtime_terminal(config)
    training = terminal["training"]; learned = terminal["evaluation"]["learned"]
    if swap_kind == "training_training":
        left = list(training["MAPR"]["updates_telemetry"][0]["shadow_receipts"]); right = list(training["MAPR"]["updates_telemetry"][1]["shadow_receipts"])
        left[0], right[0] = right[0], left[0]
        training["MAPR"]["updates_telemetry"][0]["shadow_receipts"] = tuple(left); training["MAPR"]["updates_telemetry"][1]["shadow_receipts"] = tuple(right)
    elif swap_kind == "evaluation_training":
        left = list(learned[0]["shadow_receipts"]); right = list(training["MAPR"]["updates_telemetry"][0]["shadow_receipts"])
        left[0], right[0] = right[0], left[0]
        learned[0]["shadow_receipts"] = tuple(left); training["MAPR"]["updates_telemetry"][0]["shadow_receipts"] = tuple(right)
    else:
        left = list(learned[0]["shadow_receipts"]); right = list(learned[1]["shadow_receipts"])
        left[0], right[0] = right[0], left[0]
        learned[0]["shadow_receipts"] = tuple(left); learned[1]["shadow_receipts"] = tuple(right)
    nested = tuple(receipt for arm in subject.ARMS for update in training[arm]["updates_telemetry"] for receipt in update["shadow_receipts"]) + tuple(receipt for row in (*terminal["evaluation"]["learned"], *terminal["evaluation"]["bcrh"]) for receipt in row["shadow_receipts"])
    terminal["shadow_receipts"] = nested
    terminal["host_call_ledger"] = subject._combined_host_call_ledger(config, subject._aggregate_host_call_ledger(nested), terminal["ps_b0_host_call_ledger"])
    terminal["exploratory_readout"] = subject._exploratory_readout(config, terminal["evaluation"])
    assert set(receipt["batch_id"] for receipt in nested) == subject._expected_shadow_batch_ids(config)
    with pytest.raises(subject.BExploreContractError, match="local owner/address"):
        subject.validate_runtime_terminal(config, terminal)


def test_checkpoint_snapshots_are_separate() -> None:
    model = torch.nn.Linear(2, 1, dtype=torch.float64)
    initial = subject.clone_checkpoint(model, "initial")
    with torch.no_grad():
        model.weight.add_(1)
    final = subject.clone_checkpoint(model, "final")
    subject.validate_checkpoint_pair(initial, final)
    assert initial["sha256"] != final["sha256"]


def test_learned_output_finiteness_and_probability_validator() -> None:
    valid = {"command": torch.zeros((2, 4), dtype=torch.int64), "log_probability": torch.zeros(2, dtype=torch.float64), "token_entropies": torch.zeros((2, 4), dtype=torch.float64), "value": torch.zeros(2, dtype=torch.float64), "token_probabilities": torch.full((2, 4, 3), 1 / 3, dtype=torch.float64)}
    subject._validate_model_output(valid, context="test")
    for field in ("log_probability", "token_entropies", "value", "token_probabilities"):
        bad = {name: value.clone() for name, value in valid.items()}; bad[field].view(-1)[0] = float("nan")
        with pytest.raises(subject.BExploreContractError, match="nonfinite"):
            subject._validate_model_output(bad, context="test")
    negative = {name: value.clone() for name, value in valid.items()}; negative["token_probabilities"][0, 0, 0] = -0.1
    with pytest.raises(subject.BExploreContractError, match="outside"):
        subject._validate_model_output(negative, context="test")
    mass = {name: value.clone() for name, value in valid.items()}; mass["token_probabilities"][0, 0] *= .5
    with pytest.raises(subject.BExploreContractError, match="mass"):
        subject._validate_model_output(mass, context="test")
