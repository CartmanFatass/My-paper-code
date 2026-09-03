from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict
import hashlib

import pytest

from experiments.candidates.capability_bound_semantic_currentness.omrc_b01 import addressing
from experiments.candidates.capability_bound_semantic_currentness.omrc_b01.artifact import (
    sha256_json,
)
from experiments.candidates.capability_bound_semantic_currentness.omrc_b01.b0 import ARMS
from experiments.candidates.capability_bound_semantic_currentness.omrc_b01.b1_analysis import (
    RAW_CHECKPOINT_SCHEMA,
)
from experiments.candidates.capability_bound_semantic_currentness.omrc_b01.b1_contract import (
    B1_CHECKPOINT_UPDATES,
    B1_SEEDS,
)
from experiments.candidates.capability_bound_semantic_currentness.omrc_b01.b1_engine import (
    B1_RAW_EVIDENCE_SCHEMA,
    b1_slice_counts,
)
from experiments.candidates.capability_bound_semantic_currentness.omrc_b01.b1_evidence import (
    B1EvidenceError,
    collect_complete_b1_checkpoint_records,
    reconstruct_checkpoint_records,
)
from experiments.candidates.capability_bound_semantic_currentness.omrc_b01.host import (
    DynamicHost,
)


def _digest(label: str) -> str:
    return hashlib.sha256(label.encode("ascii")).hexdigest()


def _tape_record(tape) -> dict[str, object]:
    return {
        "identity": asdict(tape.identity),
        "primitive_digest_observed": tape.primitive_digest,
        "draw_digest_observed": tape.generation_audit.draw_digest,
        "draw_count_observed": tape.generation_audit.draw_count,
    }


def _complete_raw(arm: str = ARMS[0], seed: int = B1_SEEDS[0]) -> dict[str, object]:
    host = DynamicHost(addressing.B1_RUN, seed)
    evaluation_tapes = tuple(
        host.build_stochastic(addressing.EVAL_STOCHASTIC, episode_id)
        for episode_id in range(32)
    ) + tuple(host.build_motif(episode_id) for episode_id in range(32))
    tape_digest = _digest("full-training-tapes")
    action_digest = _digest("full-action-uniforms")
    config_digest = _digest("ppo-config")
    train_ids_digest = sha256_json(list(range(384)))
    checkpoints = []
    evaluations = []
    for update in B1_CHECKPOINT_UPDATES:
        checkpoint_sha = _digest(f"{arm}/{seed}/{update}")
        checkpoints.append(
            {
                "update": update,
                "relative_path": f"checkpoint-update-{update}.pt",
                "sha256": checkpoint_sha,
                "byte_count": 1,
                "binding": {
                    "object_id": "CBSC-OMRC-B01",
                    "attempt_id": "parent-evidence-test",
                    "run_name": addressing.B1_RUN,
                    "arm": arm,
                    "seed": seed,
                    "completed_rollout_updates": update,
                    "train_episode_ids_sha256": train_ids_digest,
                    "full_training_tape_digest": tape_digest,
                    "full_action_uniform_digest": action_digest,
                    "ppo_configuration_digest": config_digest,
                    "implementation_commit": "1" * 40,
                    "source_conformance_sha256": "2" * 64,
                },
                "counters": {
                    "rollout_updates": update,
                    "adam_steps": update * 16,
                    "train_episodes": update * 8,
                    "train_transitions": update * 8 * 152,
                    "train_decisions": update * 8 * 24,
                },
                "digests": {
                    "parameter_initialization": _digest("initialization"),
                    "training_tape": tape_digest,
                    "action_uniform": action_digest,
                    "minibatch_order": _digest(f"order/{update}"),
                    "configuration": config_digest,
                },
                "model_parameter_digest": _digest(f"model/{update}"),
            }
        )
        evaluations.append(
            {
                "update": update,
                "actions": [
                    {
                        "identity": asdict(tape.identity),
                        "decision_actions": ["SAFE_FALLBACK"] * 24,
                    }
                    for tape in evaluation_tapes
                ],
                "heldout_state_observations": {
                    "model_digest_before": _digest(f"model/{update}"),
                    "model_digest_after": _digest(f"model/{update}"),
                    "training_mode_before": True,
                    "training_mode_after": True,
                    "consumed_uniform_rows": [],
                    "optimizer_digest_before": _digest(f"optimizer/{update}"),
                    "optimizer_digest_after": _digest(f"optimizer/{update}"),
                },
                "adapter_work_receipt": {
                    "byte_reads": 0,
                    "byte_writes": 0,
                    "uint8_xors": 0,
                    "appended_bytes": 0,
                    "age_increments": 0,
                },
            }
        )
    counts = b1_slice_counts(0, 48, fresh=True)
    return {
        "schema": B1_RAW_EVIDENCE_SCHEMA,
        "attempt_id": "parent-evidence-test",
        "run_name": addressing.B1_RUN,
        "arm": arm,
        "seed": seed,
        "slice": {"start_update": 0, "stop_update": 48},
        "full_bindings": {
            "train_episode_ids_sha256": train_ids_digest,
            "full_training_tape_digest": tape_digest,
            "full_action_uniform_digest": action_digest,
            "ppo_configuration_digest": config_digest,
            "implementation_commit": "1" * 40,
            "source_conformance_sha256": "2" * 64,
        },
        "train_tapes": [
            {
                "identity": {
                    "run_name": addressing.B1_RUN,
                    "seed": seed,
                    "split": addressing.TRAIN,
                    "episode_id": episode_id,
                },
                "primitive_digest_observed": _digest(f"train/{episode_id}"),
                "draw_digest_observed": _digest(f"draw/{episode_id}"),
                "draw_count_observed": 1,
            }
            for episode_id in range(384)
        ],
        "evaluation_tapes": [_tape_record(tape) for tape in evaluation_tapes],
        "rollouts": [{} for _ in range(48)],
        "training_records": {},
        "mechanical_direct": {
            "active_modes": [],
            "reset_records": [
                {
                    "name": "h0",
                    "expected_fp32_bits": ["00000000"],
                    "observed_fp32_bits": ["00000000"],
                }
            ],
            "checkpoint_records": [
                {
                    "name": "checkpoint-0",
                    "saved_sha256": _digest("saved"),
                    "loaded_sha256": _digest("saved"),
                    "expected_parameter_sha256": _digest("parameter"),
                    "restored_parameter_sha256": _digest("parameter"),
                }
            ],
            "learner_visibility_records": [
                {
                    "name": "learner-input",
                    "visible_fields": ["primitive_token", "adapter_emission"],
                    "allowed_fields": ["primitive_token", "adapter_emission"],
                }
            ],
        },
        "checkpoints_created": checkpoints,
        "evaluations": evaluations,
        "final_counters": checkpoints[-1]["counters"],
        "final_model_parameter_digest": _digest("model/48"),
        "final_optimizer_digest": _digest("optimizer/48"),
        "final_minibatch_order_digest": _digest("order/48"),
        "slice_counts": asdict(counts),
        "scientific_work_transitions": counts.scientific_work_transitions,
        "stage_measurements": [
            {
                "stage": "train",
                "wall_seconds": 1.0,
                "cpu_seconds": 1.0,
                "transitions": counts.train_transitions,
                "transitions_per_second": float(counts.train_transitions),
            },
            {
                "stage": "evaluate",
                "wall_seconds": 1.0,
                "cpu_seconds": 1.0,
                "transitions": counts.evaluation_transitions,
                "transitions_per_second": float(counts.evaluation_transitions),
            },
        ],
        "worker_count": 1,
        "threads_per_worker": 1,
        "scientific_branch": None,
    }


def test_parent_reconstructs_all_checkpoint_episodes_from_actions_and_host() -> None:
    records = reconstruct_checkpoint_records(_complete_raw())
    assert len(records) == 4
    assert [record["checkpoint_update"] for record in records] == [0, 12, 24, 48]
    assert all(record["schema"] == RAW_CHECKPOINT_SCHEMA for record in records)
    assert all(record["numerical_finite"] is True for record in records)
    assert all(record["invalid_masking_count"] == 0 for record in records)
    assert records[0]["checkpoint_identity"] == (
        f"{ARMS[0]}-{B1_SEEDS[0]}-update-0"
    )
    assert all(len(record["episodes"]) == 64 for record in records)
    assert records[0]["episodes"][0]["action_counts"] == {
        "SERVE": 0,
        "REFRESH": 0,
        "SAFE_FALLBACK": 24,
    }


def test_parent_rejects_worker_summaries_and_tape_or_action_identity_changes() -> None:
    raw = _complete_raw()
    contaminated = deepcopy(raw)
    contaminated["worker_evaluator_summary"] = {"numerical_finite": True}
    with pytest.raises(B1EvidenceError, match="fields"):
        reconstruct_checkpoint_records(contaminated)

    missing_direct = deepcopy(raw)
    missing_direct.pop("mechanical_direct")
    with pytest.raises(B1EvidenceError, match="fields|mechanical"):
        reconstruct_checkpoint_records(missing_direct)

    self_certified = deepcopy(raw)
    self_certified["mechanical_direct"]["reset_pass"] = True
    with pytest.raises(B1EvidenceError, match="mechanical"):
        reconstruct_checkpoint_records(self_certified)

    changed_tape = deepcopy(raw)
    changed_tape["evaluation_tapes"][0]["primitive_digest_observed"] = "0" * 64
    with pytest.raises(B1EvidenceError, match="primitive"):
        reconstruct_checkpoint_records(changed_tape)

    changed_action = deepcopy(raw)
    changed_action["evaluations"][0]["actions"][0]["identity"]["episode_id"] = 31
    with pytest.raises(B1EvidenceError, match="action.*identity|duplicate"):
        reconstruct_checkpoint_records(changed_action)

    invalid_masking = deepcopy(raw)
    invalid_masking["evaluations"][0]["actions"][0]["decision_actions"][0] = "WAIT"
    with pytest.raises(B1EvidenceError, match="masking census is nonzero"):
        reconstruct_checkpoint_records(invalid_masking)


def test_parent_derives_numerical_finiteness_from_reconstructed_episodes(
    monkeypatch,
) -> None:
    import experiments.candidates.capability_bound_semantic_currentness.omrc_b01.b1_evidence as module

    canonical = module.evaluate_episode

    def nonfinite_episode(tape, actions):
        record = canonical(tape, actions)
        record["return"]["float"] = float("nan")
        return record

    monkeypatch.setattr(module, "evaluate_episode", nonfinite_episode)
    with pytest.raises(B1EvidenceError, match="nonfinite"):
        reconstruct_checkpoint_records(_complete_raw())


def test_complete_collector_requires_exact_12_by_4_coverage(monkeypatch) -> None:
    import experiments.candidates.capability_bound_semantic_currentness.omrc_b01.b1_evidence as module

    inputs = []
    expected = []
    for arm in ARMS:
        for seed in B1_SEEDS:
            raw = {"arm": arm, "seed": seed}
            inputs.append(raw)
            expected.extend(
                {
                    "schema": RAW_CHECKPOINT_SCHEMA,
                    "run_name": addressing.B1_RUN,
                    "arm": arm,
                    "seed": seed,
                    "checkpoint_update": update,
                }
                for update in B1_CHECKPOINT_UPDATES
            )

    monkeypatch.setattr(
        module,
        "reconstruct_checkpoint_records",
        lambda raw: [record for record in expected if record["arm"] == raw["arm"] and record["seed"] == raw["seed"]],
    )
    collected = collect_complete_b1_checkpoint_records(inputs)
    assert len(collected) == 48
    assert [(r["arm"], r["seed"], r["checkpoint_update"]) for r in collected] == [
        (arm, seed, update)
        for arm in ARMS
        for seed in B1_SEEDS
        for update in B1_CHECKPOINT_UPDATES
    ]
    with pytest.raises(B1EvidenceError, match="48|coverage"):
        collect_complete_b1_checkpoint_records(inputs[:-1])
