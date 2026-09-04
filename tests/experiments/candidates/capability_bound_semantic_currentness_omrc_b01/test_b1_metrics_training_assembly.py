from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict
from functools import lru_cache
import gzip
import hashlib
import json
from pathlib import Path
import struct

import pytest
import torch

from experiments.candidates.capability_bound_semantic_currentness.omrc_b01.artifact import (
    canonical_json_bytes,
)
from experiments.candidates.capability_bound_semantic_currentness.omrc_b01.b1_metrics_training_assembly import (
    B1MetricsTrainingAssemblyError,
    assemble_b1_metrics_training,
    finalize_audit_table_bindings,
    finalize_audit_pointer_bindings,
    finalize_materialized_raw_facts,
)
from experiments.candidates.capability_bound_semantic_currentness.omrc_b01.b1_mechanical import (
    B1MechanicalError,
    compute_b1_mechanical,
)
from experiments.candidates.capability_bound_semantic_currentness.omrc_b01.b1_contract import (
    B1_RUN_NAME,
)
from experiments.candidates.capability_bound_semantic_currentness.omrc_b01 import addressing
from experiments.candidates.capability_bound_semantic_currentness.omrc_b01.contract import Action
from experiments.candidates.capability_bound_semantic_currentness.omrc_b01.engine import (
    _tape_primitive_digest,
    _training_action_uniforms,
)
from experiments.candidates.capability_bound_semantic_currentness.omrc_b01.host import DynamicHost
from experiments.candidates.capability_bound_semantic_currentness.omrc_b01.ppo import (
    PPOConfig,
    config_digest,
)


SEED = 21101
ARM = "STRUCT-CURRENTNESS-GRU"
DIGEST = "a" * 64


def _training_records(start_update: int = 0, stop_update: int = 48) -> dict[str, list[dict[str, object]]]:
    decisions: list[dict[str, object]] = []
    episodes: list[dict[str, object]] = []
    steps: list[dict[str, object]] = []
    for update in range(start_update, stop_update):
        for episode_id in range(update, update + 1):
            for opportunity_id in range(24):
                decisions.append({
                    "run_order": 0, "run_name": B1_RUN_NAME, "seed": SEED,
                    "arm_order": 0, "arm": ARM,
                    "training_episode_id": episode_id,
                    "opportunity_id": opportunity_id, "rollout_update": update,
                    "policy_version": update, "selected_action": opportunity_id % 3,
                    "legal_mask": [False, True, True, True],
                    "selected_log_probability": -1.0,
                    "decision_reward": 0.0, "settlement_reward": 0.0,
                    "opportunity_return": 0.0,
                })
            episodes.append({
                "run_order": 0, "run_name": B1_RUN_NAME, "seed": SEED,
                "arm_order": 0, "arm": ARM, "training_episode_id": episode_id,
                "rollout_update": update, "policy_version": update,
                "episode_return": 0.0, "action_count_serve": 8,
                "action_count_refresh": 8, "action_count_safe_fallback": 8,
            })
        for epoch in range(4):
            for minibatch in range(1):
                steps.append({
                    "run_order": 0, "run_name": B1_RUN_NAME, "seed": SEED,
                    "arm_order": 0, "arm": ARM, "rollout_update": update,
                    "ppo_epoch": epoch, "minibatch_index": minibatch,
                    "ordered_episode_ids": [update],
                    "actor_loss_fp32_bits": "00000000",
                    "value_loss_fp32_bits": "00000000",
                    "entropy_fp32_bits": "00000000",
                    "total_loss_fp32_bits": "00000000",
                    "preclip_gradient_norm_fp32_bits": "00000000",
                    "postclip_gradient_norm_fp32_bits": "00000000",
                    "optimizer_step_count": update * 4 + epoch + 1,
                    "parameter_sha256_after_step": DIGEST,
                })
    return {
        "training_decisions": decisions,
        "training_episodes": episodes,
        "optimizer_steps": steps,
    }


def _slice_counts(start_update: int, stop_update: int) -> dict[str, int]:
    checkpoints = ([0] if start_update == 0 else []) + [
        checkpoint for checkpoint in (12, 24, 48)
        if start_update < checkpoint <= stop_update
    ]
    rollout_updates = stop_update - start_update
    return {
        "rollout_updates": rollout_updates,
        "train_episodes": rollout_updates,
        "train_transitions": rollout_updates * 152,
        "evaluation_checkpoints": len(checkpoints),
        "evaluation_episodes": len(checkpoints) * 64,
        "evaluation_transitions": len(checkpoints) * 64 * 152,
    }


def _fp32(value: object) -> float:
    return struct.unpack(">f", struct.pack(">f", float(value)))[0]


def _json_digest(value: object) -> str:
    payload = json.dumps(
        value, ensure_ascii=True, separators=(",", ":"), sort_keys=True
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


@lru_cache(maxsize=1)
def _full_panel_bindings() -> tuple[str, str]:
    host = DynamicHost(B1_RUN_NAME, SEED)
    tapes = tuple(host.build_stochastic(addressing.TRAIN, episode) for episode in range(48))
    _, action_digest, _ = _training_action_uniforms(tapes, B1_RUN_NAME, SEED)
    return _tape_primitive_digest(tapes), action_digest


@lru_cache(maxsize=8)
def _canonical_slice_evidence(start_update: int, stop_update: int) -> dict[str, object]:
    host = DynamicHost(B1_RUN_NAME, SEED)
    decisions: list[dict[str, object]] = []
    episodes: list[dict[str, object]] = []
    steps: list[dict[str, object]] = []
    rollouts: list[dict[str, object]] = []
    order_digest = hashlib.sha256(b"").hexdigest()
    decision_rows = list(range(12, 152, 6))
    forced_rows = [row for row in range(152) if row not in decision_rows]
    for update in range(stop_update):
        epoch_orders: list[tuple[int, ...]] = []
        for epoch in range(4):
            order, addresses = (0,), ()
            payload = {
                "update": update, "epoch": epoch, "order": list(order),
                "addresses": [list(address) for address in addresses],
            }
            encoded = json.dumps(
                payload, ensure_ascii=True, separators=(",", ":"), sort_keys=True
            ).encode("utf-8")
            order_digest = hashlib.sha256(bytes.fromhex(order_digest) + encoded).hexdigest()
            epoch_orders.append(order)
        if update < start_update:
            continue
        tapes = tuple(
            host.build_stochastic(addressing.TRAIN, episode)
            for episode in range(update, update + 1)
        )
        _, chunk_action_digest, uniform_records = _training_action_uniforms(
            tapes, B1_RUN_NAME, SEED
        )
        action_traces: list[dict[str, object]] = []
        reward_traces: list[dict[str, object]] = []
        for tape in tapes:
            action_names: list[str] = []
            decision_rewards: list[float] = []
            settlement_rewards: list[float] = []
            reward_tensor = torch.zeros(152, dtype=torch.float32)
            action_counts = [0, 0, 0]
            for opportunity in range(24):
                selected = opportunity % 3
                action = Action(selected + 1)
                ledger = tape.evaluator().ledger(opportunity, action)
                decision_reward = _fp32(ledger.decision_reward)
                settlement_reward = _fp32(ledger.settlement_reward)
                opportunity_return = _fp32(decision_reward + settlement_reward)
                action_names.append(action.name)
                decision_rewards.append(decision_reward)
                settlement_rewards.append(settlement_reward)
                action_counts[selected] += 1
                reward_tensor[12 + 6 * opportunity] = decision_reward
                reward_tensor[13 + 6 * opportunity] = settlement_reward
                decisions.append({
                    "run_order": 0, "run_name": B1_RUN_NAME, "seed": SEED,
                    "arm_order": 0, "arm": ARM,
                    "training_episode_id": tape.identity.episode_id,
                    "opportunity_id": opportunity, "rollout_update": update,
                    "policy_version": update, "selected_action": selected,
                    "legal_mask": [False, True, True, True],
                    "selected_log_probability": -1.0,
                    "decision_reward": decision_reward,
                    "settlement_reward": settlement_reward,
                    "opportunity_return": opportunity_return,
                })
            episodes.append({
                "run_order": 0, "run_name": B1_RUN_NAME, "seed": SEED,
                "arm_order": 0, "arm": ARM,
                "training_episode_id": tape.identity.episode_id,
                "rollout_update": update, "policy_version": update,
                "episode_return": float(reward_tensor.sum(dtype=torch.float32).item()),
                "action_count_serve": action_counts[0],
                "action_count_refresh": action_counts[1],
                "action_count_safe_fallback": action_counts[2],
            })
            action_traces.append({
                "identity": asdict(tape.identity), "decision_actions": action_names,
            })
            reward_traces.append({
                "identity": asdict(tape.identity),
                "decision_rewards": decision_rewards,
                "settlement_rewards": settlement_rewards,
                "nonzero_outside_ledger_rows": [],
            })
        for epoch, order in enumerate(epoch_orders):
            for minibatch in range(1):
                selected = order
                steps.append({
                    "run_order": 0, "run_name": B1_RUN_NAME, "seed": SEED,
                    "arm_order": 0, "arm": ARM, "rollout_update": update,
                    "ppo_epoch": epoch, "minibatch_index": minibatch,
                    "ordered_episode_ids": [update + index for index in selected],
                    "actor_loss_fp32_bits": "00000000",
                    "value_loss_fp32_bits": "00000000",
                    "entropy_fp32_bits": "00000000",
                    "total_loss_fp32_bits": "00000000",
                    "preclip_gradient_norm_fp32_bits": "00000000",
                    "postclip_gradient_norm_fp32_bits": "00000000",
                    "optimizer_step_count": update * 4 + epoch + 1,
                    "parameter_sha256_after_step": DIGEST,
                })
        optimizer_digest = hashlib.sha256(f"optimizer:{update}".encode()).hexdigest()
        counters = {
            "rollout_updates": update + 1, "adam_steps": (update + 1) * 4,
            "train_episodes": update + 1,
            "train_transitions": (update + 1) * 152,
            "train_decisions": (update + 1) * 24,
        }
        rollouts.append({
            "update_before": update, "update_after": update + 1,
            "tapes": [{
                "identity": asdict(tape.identity),
                "primitive_digest_observed": tape.primitive_digest,
                "draw_digest_observed": tape.generation_audit.draw_digest,
                "draw_count_observed": tape.generation_audit.draw_count,
            } for tape in tapes],
            "raw_rollout": {
                "observation_shape": [1, 152, 168],
                "actions": action_traces, "uniforms": uniform_records,
                "uniforms_consumed_rows": [decision_rows[:]],
                "forced_wait_rows": [forced_rows[:]],
                "rewards": reward_traces,
                "terminated_rows": [[151]],
            },
            "chunk_action_uniform_digest": chunk_action_digest,
            "counters_after": counters,
            "model_parameter_digest_after": DIGEST,
            "optimizer_digest_after": optimizer_digest,
            "minibatch_order_digest_after": order_digest,
        })
    tape_digest, full_action_digest = _full_panel_bindings()
    return {
        "training_records": {
            "training_decisions": decisions,
            "training_episodes": episodes,
            "optimizer_steps": steps,
        },
        "rollouts": rollouts,
        "full_training_tape_digest": tape_digest,
        "full_action_uniform_digest": full_action_digest,
        "final_counters": rollouts[-1]["counters_after"],
        "final_model_parameter_digest": DIGEST,
        "final_optimizer_digest": rollouts[-1]["optimizer_digest_after"],
        "final_minibatch_order_digest": rollouts[-1]["minibatch_order_digest_after"],
    }


def _raw_slice(start_update: int = 0, stop_update: int = 48) -> dict[str, object]:
    counts = _slice_counts(start_update, stop_update)
    evidence = deepcopy(_canonical_slice_evidence(start_update, stop_update))
    return {
        "attempt_id": "test-attempt", "run_name": B1_RUN_NAME,
        "seed": SEED, "arm": ARM, "scientific_branch": None,
        "slice": {"start_update": start_update, "stop_update": stop_update},
        "training_records": evidence["training_records"],
        "full_bindings": {
            "full_training_tape_digest": evidence["full_training_tape_digest"],
            "full_action_uniform_digest": evidence["full_action_uniform_digest"],
            "ppo_configuration_digest": config_digest(PPOConfig()),
            "implementation_commit": "b" * 40,
            "source_conformance_sha256": "c" * 64,
        },
        "slice_counts": counts,
        "scientific_work_transitions": counts["train_transitions"] + counts["evaluation_transitions"],
        "stage_measurements": deepcopy(_telemetry(start_update, stop_update)["measurement"]["stage_measurements"]),
        "rollouts": evidence["rollouts"],
        "final_counters": evidence["final_counters"],
        "final_model_parameter_digest": evidence["final_model_parameter_digest"],
        "final_optimizer_digest": evidence["final_optimizer_digest"],
        "final_minibatch_order_digest": evidence["final_minibatch_order_digest"],
        "evaluations": [{
            "update": 48,
            "heldout_state_observations": {
                "model_digest_before": DIGEST, "model_digest_after": DIGEST,
                "optimizer_digest_before": "d" * 64,
                "optimizer_digest_after": "d" * 64,
            },
        }],
        "mechanical_direct": {
            "active_modes": [],
            "reset_records": [{
                "name": "h0", "expected_fp32_bits": ["00000000"],
                "observed_fp32_bits": ["00000000"],
            }],
            "checkpoint_records": [{
                "name": "checkpoint-48", "saved_sha256": DIGEST,
                "loaded_sha256": DIGEST,
                "expected_parameter_sha256": DIGEST,
                "restored_parameter_sha256": DIGEST,
            }],
            "learner_visibility_records": [{
                "name": "learner-input", "visible_fields": ["primitive_token"],
                "allowed_fields": ["primitive_token"],
            }],
        },
    }


def _admission(attempt_order: int = 0) -> dict[str, object]:
    return {
        "attempt_order": attempt_order,
        "attempt_id": "test-attempt", "run_name": B1_RUN_NAME,
        "seed": SEED, "arm": ARM, "receipt_sha256": DIGEST,
        "available_physical_bytes": 5 * 1024**3,
        "effective_available_bytes": 5 * 1024**3,
    }


def _telemetry(
    start_update: int = 0, stop_update: int = 48, attempt_order: int = 0,
) -> dict[str, object]:
    counts = _slice_counts(start_update, stop_update)
    transitions = counts["train_transitions"] + counts["evaluation_transitions"]
    wall = 10.0
    measurement = {
        "measurement_complete": True, "measurement_source": "TEST_ONLY",
        "sample_interval_seconds": 0.05, "sample_count": 2,
        "end_to_end_wall_seconds": wall, "end_to_end_cpu_seconds": wall,
        "cpu_core_equivalents": 1.0, "cpu_occupancy_fraction": 1.0,
        "process_tree_peak_rss_bytes": 1024, "peak_process_count": 1,
        "peak_thread_count": 1, "worker_count": 1, "threads_per_worker": 1,
        "io_read_bytes": 0, "io_write_bytes": 0,
        "scratch_high_water_bytes": 0, "durable_high_water_bytes": 1024,
        "scientific_work_transitions": transitions,
        "scientific_work_transitions_per_second": transitions / wall,
        "stage_measurements": [
            {"stage": "train", "wall_seconds": wall / 2, "cpu_seconds": wall / 2,
             "transitions": counts["train_transitions"],
             "transitions_per_second": counts["train_transitions"] / (wall / 2)},
            {"stage": "evaluate", "wall_seconds": wall / 2, "cpu_seconds": wall / 2,
             "transitions": counts["evaluation_transitions"],
             "transitions_per_second": counts["evaluation_transitions"] / (wall / 2)},
        ],
    }
    return {
        "attempt_order": attempt_order,
        "attempt_id": "test-attempt", "run_name": B1_RUN_NAME,
        "seed": SEED, "arm": ARM, "measurement": measurement,
    }


def _policy_replay_resources(indices: tuple[int, ...] = (1, 5)) -> dict[str, object]:
    admissions: list[dict[str, object]] = []
    telemetry: list[dict[str, object]] = []
    slots = ((21101, "RAW-GRU"), (21121, "RAW-GRU"))
    for slot_index, (seed, arm) in zip(indices, slots, strict=True):
        base = {
            "run_order": 0, "invocation_kind": "POLICY_REPLAY",
            "original_slot_index": slot_index, "attempt_order": 0,
            "seed": seed, "arm_order": 1, "run_name": B1_RUN_NAME,
            "arm": arm, "attempt_id": "test-attempt",
            "slice_start_update": None, "slice_stop_update": None,
        }
        admissions.append({
            **base, "receipt_sha256": hashlib.sha256(
                f"admission:{slot_index}".encode()
            ).hexdigest(),
            "bound_admission_relative_path": f"policy-replay/{slot_index:02d}/admission.json",
            "raw_receipt_relative_path": f"policy-replay/{slot_index:02d}/receipt.json",
            "raw_receipt_sha256": hashlib.sha256(
                f"receipt:{slot_index}".encode()
            ).hexdigest(),
            "available_physical_bytes": 5 * 1024**3,
            "effective_available_bytes": 5 * 1024**3,
        })
        measurement = deepcopy(_telemetry()["measurement"])
        telemetry.append({
            **base, "measurement": measurement,
            "telemetry_relative_path": f"policy-replay/{slot_index:02d}/telemetry.json",
            "telemetry_sha256": hashlib.sha256(
                f"telemetry:{slot_index}".encode()
            ).hexdigest(),
        })
    return {"resource_admissions": admissions, "telemetry": telemetry}


def _shared_policy_tables() -> tuple[dict[str, object], dict[str, object]]:
    truth: list[dict[str, object]] = []
    policy: list[dict[str, object]] = []
    curves: list[dict[str, object]] = []
    for seed in (21101, 21121, 21143):
        for split_order, split in ((1, "EVAL_STOCHASTIC"), (2, "EVAL_MOTIF")):
            tape_id = 0
            curves.append({
                "run_order": 0, "seed": seed, "split_order": split_order,
                "tape_id": tape_id, "arm_order": 1,
                "episode_return_update_0": {"numerator": 2, "denominator": 1},
                "episode_return_update_12": {"numerator": 2, "denominator": 1},
                "episode_return_update_24": {"numerator": 2, "denominator": 1},
                "episode_return_update_48": {"numerator": 2, "denominator": 1},
            })
            for opportunity_id in range(24):
                truth.append({
                    "run_order": 0, "run_name": B1_RUN_NAME, "seed": seed,
                    "split_order": split_order, "split": split,
                    "tape_id": tape_id, "opportunity_id": opportunity_id,
                    "request_active": True, "access_gated": False,
                    "presented_body_native_neutral": False,
                    "address_match_truth": True,
                    "payload_source_match_truth": True,
                    "content_match_truth": True, "owner_match_truth": True,
                    "epoch_match_truth": True,
                    "oracle_action": opportunity_id % 3,
                    "refresh_total_value": {"numerator": 0, "denominator": 1},
                    "safe_fallback_total_value": {"numerator": 0, "denominator": 1},
                })
                for checkpoint_update in (0, 12, 24, 48):
                    policy.append({
                        "run_order": 0, "seed": seed,
                        "checkpoint_update": checkpoint_update,
                        "split_order": split_order, "tape_id": tape_id,
                        "opportunity_id": opportunity_id, "arm_order": 1,
                        "legal_action_mask": [False, True, True, True],
                        "actor_logits_fp32_bits": [0, 0, 0, 0],
                        "critic_value_fp32_bits": 0,
                        "selected_action": 0 if opportunity_id < 20 else 1,
                        "selected_action_log_probability_fp32_bits": 0,
                    })
    shared = {
        "evaluator_decision_truth": truth,
        "motif_twin_index": [{
            "run_order": 0, "seed": 21101, "motif_family": 0,
            "tape_id": 0, "pair_id": "21101:0:0", "member_role": "A",
        }, {
            "run_order": 0, "seed": 21101, "motif_family": 0,
            "tape_id": 0, "pair_id": "21101:0:0", "member_role": "B",
        }],
    }
    return shared, {
        "policy_decisions": policy,
        "per_tape_curves": curves,
        "execution_mode_records": [
            {"run_order": 0, "seed": seed, "arm_order": 1,
             "checkpoint_update": checkpoint, "active_modes": []}
            for seed in (21101, 21121, 21143)
            for checkpoint in (0, 12, 24, 48)
        ],
    }


def test_test_only_assembly_rehydrates_training_and_computes_direct_mechanical() -> None:
    shared, policy = _shared_policy_tables()
    result = assemble_b1_metrics_training(
        raw_slice_groups=[[_raw_slice()]], admission_groups=[[_admission()]],
        telemetry_groups=[[_telemetry()]], shared_tables=shared,
        policy_tables=policy, test_only=True,
    )
    assert len(result["tables"]["training_decisions"]) == 1_152
    assert len(result["tables"]["training_episodes"]) == 48
    assert len(result["tables"]["optimizer_steps"]) == 192
    assert result["tables"]["resource_admissions"][0]["run_order"] == 0
    assert result["tables"]["telemetry"][0]["attempt_order"] == 0
    assert [row["seed"] for row in result["tables"]["raw_competence"]] == [21101, 21121, 21143]
    assert [row["raw_competence_pass"] for row in result["tables"]["raw_competence"]] == [None] * 3
    assert all(
        row["components"]["record_integrity_pass"] is None
        for row in result["tables"]["raw_competence"]
    )
    assert "mechanical" not in result
    assert result["prepublication_status"] == {
        "status": "PENDING_MATERIALIZATION_REREAD",
        "mechanical_attempt_complete": False,
        "mechanical_conformance_pass": False,
        "scientific_packet_readable": False,
        "publication_digests": None,
    }
    assert result["raw_competence_truth_authority"] is False
    assert result["formal_readiness_authority"] is False
    assert result["upstream_instrumentation_gaps"] == []
    rollout_audits = [
        row for row in result["tables"]["audits"]
        if ":ROLLOUT:" in row["audit_code"]
        and row["fact_name"].startswith("rollout-update-")
    ]
    assert len(rollout_audits) == 48
    assert rollout_audits[0]["authority_type"] == "DIRECT_RAW_FACT"
    assert rollout_audits[0]["source_raw_slice"] == {
        "attempt_id": "test-attempt", "seed": SEED, "arm_order": 0,
        "slice_start_update": 0, "slice_stop_update": 48,
        "attempt_order": 0,
    }
    assert rollout_audits[0]["expected"] is None
    assert rollout_audits[0]["observed"] is None
    assert rollout_audits[0]["expected_sha256"] == rollout_audits[0]["actual_sha256"]
    assert rollout_audits[0]["json_pointer"] == "/raw_evidence/rollouts/0"
    assert rollout_audits[0]["payload_shape"] == []
    assert rollout_audits[0]["payload_dtype"] == (
        "float64-json+int+string"
    )


def test_formal_shape_and_missing_direct_instrumentation_fail_closed() -> None:
    shared, policy = _shared_policy_tables()
    arguments = {
        "raw_slice_groups": [[_raw_slice()]],
        "admission_groups": [[_admission()]],
        "telemetry_groups": [[_telemetry()]],
        "shared_tables": shared, "policy_tables": policy,
    }
    with pytest.raises(B1MetricsTrainingAssemblyError, match="formal arm-seed group shape"):
        assemble_b1_metrics_training(**arguments, test_only=False)

    missing = deepcopy(arguments)
    missing["raw_slice_groups"][0][0].pop("mechanical_direct")
    with pytest.raises(B1MetricsTrainingAssemblyError, match="UPSTREAM_INSTRUMENTATION_GAP.*mechanical_direct"):
        assemble_b1_metrics_training(**missing, test_only=True)

    incomplete_profile = deepcopy(arguments)
    incomplete_profile["policy_tables"]["policy_decisions"].pop()
    with pytest.raises(B1MetricsTrainingAssemblyError, match="TEST_ONLY RAW profile"):
        assemble_b1_metrics_training(**incomplete_profile, test_only=True)


def test_three_fresh_slices_join_telemetry_without_last_value_laundering() -> None:
    shared, policy = _shared_policy_tables()
    intervals = ((0, 12), (12, 24), (24, 48))
    result = assemble_b1_metrics_training(
        raw_slice_groups=[[_raw_slice(start, stop) for start, stop in intervals]],
        admission_groups=[[_admission(order) for order in range(3)]],
        telemetry_groups=[[
            _telemetry(start, stop, order)
            for order, (start, stop) in enumerate(intervals)
        ]],
        shared_tables=shared, policy_tables=policy, test_only=True,
    )
    telemetry_work = next(
        row for row in result["prepublication_raw_facts"]["work_bindings"]
        if row["name"].endswith("telemetry-work")
    )
    assert telemetry_work == {
        "name": "21101:0:telemetry-work",
        "expected_count": 46_208,
        "observed_count": 46_208,
    }
    assert [row["attempt_order"] for row in result["tables"]["telemetry"]] == [0, 1, 2]


@pytest.mark.parametrize("defect", ("missing", "duplicate", "reorder", "mismatch"))
def test_slice_telemetry_join_rejects_missing_duplicate_reorder_and_work_mismatch(
    defect: str,
) -> None:
    shared, policy = _shared_policy_tables()
    intervals = ((0, 12), (12, 24), (24, 48))
    raw = [_raw_slice(start, stop) for start, stop in intervals]
    admissions = [_admission(order) for order in range(3)]
    telemetry = [
        _telemetry(start, stop, order)
        for order, (start, stop) in enumerate(intervals)
    ]
    if defect == "missing":
        telemetry.pop()
    elif defect == "duplicate":
        telemetry[1]["attempt_order"] = 0
    elif defect == "reorder":
        telemetry[0], telemetry[1] = telemetry[1], telemetry[0]
    else:
        measurement = telemetry[1]["measurement"]
        measurement["scientific_work_transitions"] += 1
        measurement["scientific_work_transitions_per_second"] = (
            measurement["scientific_work_transitions"]
            / measurement["end_to_end_wall_seconds"]
        )
        measurement["stage_measurements"][0]["transitions"] += 1
        measurement["stage_measurements"][0]["transitions_per_second"] = (
            measurement["stage_measurements"][0]["transitions"]
            / measurement["stage_measurements"][0]["wall_seconds"]
        )
    with pytest.raises(B1MetricsTrainingAssemblyError, match="inventory|attempt_order|slice work"):
        assemble_b1_metrics_training(
            raw_slice_groups=[raw], admission_groups=[admissions],
            telemetry_groups=[telemetry], shared_tables=shared,
            policy_tables=policy, test_only=True,
        )


def test_prepublication_source_config_self_comparison_cannot_claim_publication_pass() -> None:
    shared, policy = _shared_policy_tables()
    result = assemble_b1_metrics_training(
        raw_slice_groups=[[_raw_slice()]], admission_groups=[[_admission()]],
        telemetry_groups=[[_telemetry()]], shared_tables=shared,
        policy_tables=policy, test_only=True,
    )
    prewrite = result["prepublication_raw_facts"]
    assert prewrite["digest_bindings"] == {
        "status": "PENDING_MATERIALIZATION_REREAD",
        "records": [],
    }
    assert "mechanical" not in result
    with pytest.raises(B1MechanicalError, match="digest_bindings must be a nonempty list"):
        compute_b1_mechanical(prewrite, result["raw_competence_inputs"])

    source_config_only = [{
        "name": "source-config-self-comparison",
        "expected_sha256": DIGEST, "actual_sha256": DIGEST,
        "expected_byte_count": 1, "actual_byte_count": 1,
    }]
    with pytest.raises(B1MetricsTrainingAssemblyError, match="three direct materialized digest inventories"):
        finalize_materialized_raw_facts(
            prewrite,
            table_digest_records=source_config_only,
            artifact_digest_records=[], checkpoint_digest_records=[],
        )


def test_materialized_digest_finalizer_preserves_actual_mismatch_for_final_compute() -> None:
    shared, policy = _shared_policy_tables()
    result = assemble_b1_metrics_training(
        raw_slice_groups=[[_raw_slice()]], admission_groups=[[_admission()]],
        telemetry_groups=[[_telemetry()]], shared_tables=shared,
        policy_tables=policy, test_only=True,
    )
    direct = {
        "expected_sha256": DIGEST, "actual_sha256": DIGEST,
        "expected_byte_count": 10, "actual_byte_count": 10,
    }
    finalized = finalize_materialized_raw_facts(
        result["prepublication_raw_facts"],
        table_digest_records=[{"name": "training-table", **direct}],
        artifact_digest_records=[{"name": "complete-artifact", **direct}],
        checkpoint_digest_records=[{
            "name": "checkpoint", **direct, "actual_sha256": "f" * 64,
        }],
    )
    mechanical = compute_b1_mechanical(finalized, result["raw_competence_inputs"])
    assert mechanical["mechanical_components"]["publication_digests"] is False
    assert "PUBLICATION_DIGEST_FAILURE" in mechanical["blocking_audit_codes"]


def test_audits_preserve_adverse_reset_and_checkpoint_rows_with_raw_slice_identity() -> None:
    shared, policy = _shared_policy_tables()
    raw = _raw_slice()
    raw["mechanical_direct"]["reset_records"][0]["observed_fp32_bits"] = ["3f800000"]
    raw["mechanical_direct"]["checkpoint_records"][0]["loaded_sha256"] = "f" * 64
    result = assemble_b1_metrics_training(
        raw_slice_groups=[[raw]], admission_groups=[[_admission()]],
        telemetry_groups=[[_telemetry()]], shared_tables=shared,
        policy_tables=policy, test_only=True,
    )
    audits = result["tables"]["audits"]
    assert len(audits) != 15
    assert all("raw_record_count" not in row for row in audits)
    reset = next(row for row in audits if ":RESET:" in row["audit_code"])
    checkpoint = next(row for row in audits if ":CHECKPOINT:" in row["audit_code"])
    assert reset["expected"] is None and reset["observed"] is None
    assert checkpoint["expected"] is None and checkpoint["observed"] is None
    assert reset["expected_sha256"] != reset["actual_sha256"]
    assert checkpoint["expected_sha256"] != checkpoint["actual_sha256"]
    assert reset["binding_status"] == "DIRECT_RAW_FACT_ADVERSE"
    assert checkpoint["binding_status"] == "DIRECT_RAW_FACT_ADVERSE"
    assert reset["source_raw_slice"] == {
        "attempt_id": "test-attempt", "seed": 21101, "arm_order": 0,
        "slice_start_update": 0, "slice_stop_update": 48,
        "attempt_order": 0,
    }


def test_audit_table_binding_rejects_missing_and_tampered_materialized_authority() -> None:
    shared, policy = _shared_policy_tables()
    result = assemble_b1_metrics_training(
        raw_slice_groups=[[_raw_slice()]], admission_groups=[[_admission()]],
        telemetry_groups=[[_telemetry()]], shared_tables=shared,
        policy_tables=policy, test_only=True,
    )
    audits = result["tables"]["audits"]
    table_rows = [row for row in audits if row["authority_type"] == "CANONICAL_TABLE_AUTHORITY"]
    materialized = [{
        "source_table": row["source_table"],
        "actual_sha256": row["expected_sha256"],
        "actual_row_count": row["expected"]["row_count"],
        "actual_first_key": row["source_key_range"]["first_key"],
        "actual_last_key": row["source_key_range"]["last_key"],
    } for row in table_rows]
    with pytest.raises(B1MetricsTrainingAssemblyError, match="inventory.*coverage"):
        finalize_audit_table_bindings(audits, materialized[:-1])
    tampered = deepcopy(materialized)
    tampered[0]["actual_sha256"] = "f" * 64
    with pytest.raises(B1MetricsTrainingAssemblyError, match="reread binding differs"):
        finalize_audit_table_bindings(audits, tampered)


@pytest.mark.parametrize(
    ("defect", "audit_code"),
    (
        ("u64", "ACTION_U64_MISMATCH"),
        ("consumed", "ACTION_CONSUMPTION_MISMATCH"),
        ("reward", "REWARD_LEDGER_MISMATCH"),
        ("terminal", "TERMINAL_ROW_MISMATCH"),
        ("order", "MINIBATCH_ORDER_CHAIN_MISMATCH"),
    ),
)
def test_rollout_rng_audit_rejects_mutated_direct_evidence(
    defect: str, audit_code: str,
) -> None:
    shared, policy = _shared_policy_tables()
    raw = _raw_slice()
    rollout = raw["rollouts"][0]
    if defect == "u64":
        rollout["raw_rollout"]["uniforms"][0]["u64"] ^= 1
    elif defect == "consumed":
        rollout["raw_rollout"]["uniforms_consumed_rows"][0].pop()
    elif defect == "reward":
        rollout["raw_rollout"]["rewards"][0]["decision_rewards"][0] = 99.0
    elif defect == "terminal":
        rollout["raw_rollout"]["terminated_rows"][0] = [150]
    else:
        rollout["minibatch_order_digest_after"] = "f" * 64
    with pytest.raises(
        B1MetricsTrainingAssemblyError,
        match=f"ROLLOUT_AUDIT_ADVERSE:{audit_code}",
    ):
        assemble_b1_metrics_training(
            raw_slice_groups=[[raw]], admission_groups=[[_admission()]],
            telemetry_groups=[[_telemetry()]], shared_tables=shared,
            policy_tables=policy, test_only=True,
        )


def test_pointer_audits_reread_worker_source_and_reject_descriptor_tamper(
    tmp_path: Path,
) -> None:
    shared, policy = _shared_policy_tables()
    raw = _raw_slice()
    wrapper = {
        "schema": "test-worker-result", "raw_evidence": raw,
        "scientific_branch": None,
    }
    payload = canonical_json_bytes(wrapper) + b"\n"
    relative = f"workers/00-seed-{SEED}-{ARM}/slice-00-48/result.json.gz"
    path = tmp_path / relative
    path.parent.mkdir(parents=True)
    path.write_bytes(gzip.compress(payload, compresslevel=9, mtime=0))
    sources = [[{
        "source_relative_path": relative,
        "source_file_sha256": hashlib.sha256(payload).hexdigest(),
        "raw_json_pointer": "/raw_evidence",
    }]]
    result = assemble_b1_metrics_training(
        raw_slice_groups=[[raw]], raw_source_groups=sources,
        admission_groups=[[_admission()]], telemetry_groups=[[_telemetry()]],
        shared_tables=shared, policy_tables=policy, test_only=True,
    )
    audits = result["tables"]["audits"]
    bound = finalize_audit_pointer_bindings(audits, tmp_path)
    direct = [row for row in bound if row["authority_type"] == "DIRECT_RAW_FACT"]
    assert direct
    assert all(row["binding_status"].startswith("BOUND_SOURCE_REREAD") for row in direct)

    pointer_tamper = deepcopy(audits)
    pointer_row = next(row for row in pointer_tamper if row["authority_type"] == "DIRECT_RAW_FACT")
    pointer_row["json_pointer"] += "/missing"
    with pytest.raises(B1MetricsTrainingAssemblyError, match="JSON pointer"):
        finalize_audit_pointer_bindings(pointer_tamper, tmp_path)

    source_tamper = deepcopy(audits)
    source_row = next(row for row in source_tamper if row["authority_type"] == "DIRECT_RAW_FACT")
    source_row["source_file_sha256"] = "f" * 64
    with pytest.raises(B1MetricsTrainingAssemblyError, match="source file SHA"):
        finalize_audit_pointer_bindings(source_tamper, tmp_path)

    nonzero_tamper = deepcopy(audits)
    nonzero_row = next(row for row in nonzero_tamper if row["authority_type"] == "DIRECT_RAW_FACT")
    nonzero_row["payload_nonzero_count"] += 1
    with pytest.raises(B1MetricsTrainingAssemblyError, match="payload metadata"):
        finalize_audit_pointer_bindings(nonzero_tamper, tmp_path)


def test_policy_replay_resources_join_canonical_tables_and_mechanical_inventory() -> None:
    shared, policy = _shared_policy_tables()
    replay = _policy_replay_resources()
    result = assemble_b1_metrics_training(
        raw_slice_groups=[[_raw_slice()]], admission_groups=[[_admission()]],
        telemetry_groups=[[_telemetry()]], policy_replay_resources=replay,
        shared_tables=shared, policy_tables=policy, test_only=True,
    )
    admissions = result["tables"]["resource_admissions"]
    telemetry = result["tables"]["telemetry"]
    assert [row["invocation_kind"] for row in admissions] == [
        "TRAINING_SLICE", "POLICY_REPLAY", "POLICY_REPLAY",
    ]
    assert [(row["original_slot_index"], row["attempt_order"]) for row in admissions] == [
        (0, 0), (1, 0), (5, 0),
    ]
    assert [
        (row["invocation_kind"], row["original_slot_index"])
        for row in telemetry
    ] == [
        ("TRAINING_SLICE", 0), ("POLICY_REPLAY", 1), ("POLICY_REPLAY", 5),
    ]
    resources = result["prepublication_raw_facts"]["resources"]
    assert [row["invocation_id"] for row in resources] == [
        "TRAINING_SLICE:00:00", "POLICY_REPLAY:01", "POLICY_REPLAY:05",
    ]

    dropped = deepcopy(replay)
    dropped["telemetry"].pop()
    with pytest.raises(B1MetricsTrainingAssemblyError, match="replay.*coverage"):
        assemble_b1_metrics_training(
            raw_slice_groups=[[_raw_slice()]], admission_groups=[[_admission()]],
            telemetry_groups=[[_telemetry()]], policy_replay_resources=dropped,
            shared_tables=shared, policy_tables=policy, test_only=True,
        )
    reordered = deepcopy(replay)
    reordered["resource_admissions"].reverse()
    with pytest.raises(B1MetricsTrainingAssemblyError, match="replay.*order"):
        assemble_b1_metrics_training(
            raw_slice_groups=[[_raw_slice()]], admission_groups=[[_admission()]],
            telemetry_groups=[[_telemetry()]], policy_replay_resources=reordered,
            shared_tables=shared, policy_tables=policy, test_only=True,
        )
    tampered = deepcopy(replay)
    tampered["telemetry"][0]["seed"] = 999
    with pytest.raises(B1MetricsTrainingAssemblyError, match="replay.*identity"):
        assemble_b1_metrics_training(
            raw_slice_groups=[[_raw_slice()]], admission_groups=[[_admission()]],
            telemetry_groups=[[_telemetry()]], policy_replay_resources=tampered,
            shared_tables=shared, policy_tables=policy, test_only=True,
        )


@pytest.mark.parametrize("defect", [None, "work", "stage"])
def test_missing_resources_preserve_raw_work_reconciliation(defect):
    shared, policy = _shared_policy_tables()
    raw = _raw_slice()
    if defect == "work":
        raw["scientific_work_transitions"] += 1
    elif defect == "stage":
        raw["stage_measurements"][0]["transitions"] += 1
    kwargs = dict(raw_slice_groups=[[raw]], admission_groups=[[_admission()]],
        telemetry_groups=[[{**_telemetry(), "measurement": None}]],
        shared_tables=shared, policy_tables=policy, test_only=True)
    if defect:
        with pytest.raises(B1MetricsTrainingAssemblyError, match="raw slice work"):
            assemble_b1_metrics_training(**kwargs)
    else:
        packet = assemble_b1_metrics_training(**kwargs)
        measured = packet["tables"]["telemetry"][0]["measurement"]
        assert measured["resources_unmeasured"] is True
        assert measured["process_tree_peak_rss_bytes"] is None
        assert measured["scientific_work_transitions"] == raw["scientific_work_transitions"]


@pytest.mark.parametrize("rss,cap", [(1024, None), (10**15, False)])
def test_partial_samples_remain_numeric_without_claiming_full_caps(rss, cap):
    shared, policy = _shared_policy_tables()
    telemetry = _telemetry()
    telemetry["measurement"].update(measurement_complete=False, process_tree_peak_rss_bytes=rss)
    packet = assemble_b1_metrics_training(raw_slice_groups=[[_raw_slice()]],
        admission_groups=[[_admission()]], telemetry_groups=[[telemetry]],
        shared_tables=shared, policy_tables=policy, test_only=True)
    measurement = packet["tables"]["telemetry"][0]["measurement"]
    assert measurement["resources_unmeasured"] is True
    assert measurement["process_tree_peak_rss_bytes"] == rss
    from experiments.candidates.capability_bound_semantic_currentness.omrc_b01.b1_mechanical import _compute_mechanical_components
    from tests.experiments.candidates.capability_bound_semantic_currentness_omrc_b01.test_b1_mechanical import _facts
    facts = _facts()
    facts["resources"] = packet["prepublication_raw_facts"]["resources"]
    assert _compute_mechanical_components(facts)["resource_caps"] is cap
