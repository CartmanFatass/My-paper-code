from __future__ import annotations

from fractions import Fraction
import hashlib
import io

import pytest
import torch

from experiments.candidates.capability_bound_semantic_currentness.omrc_b01 import addressing
from experiments.candidates.capability_bound_semantic_currentness.omrc_b01.b1_policy_records import (
    B1PolicyRecordError,
    build_checkpoint_policy_records,
    build_complete_policy_curves,
    build_literal_null_manifest_fields,
    build_policy_support_signature_counts,
)
from experiments.candidates.capability_bound_semantic_currentness.omrc_b01.b1_engine import (
    B1CheckpointBinding,
    capture_b1_checkpoint,
)
from experiments.candidates.capability_bound_semantic_currentness.omrc_b01.b1_shared_tables import (
    build_b1_shared_truth_tables,
)
from experiments.candidates.capability_bound_semantic_currentness.omrc_b01.contract import Action
from experiments.candidates.capability_bound_semantic_currentness.omrc_b01.host import DynamicHost
from experiments.candidates.capability_bound_semantic_currentness.omrc_b01.model import (
    CommonRecurrentActorCritic,
    model_parameter_digest,
)
from experiments.candidates.capability_bound_semantic_currentness.omrc_b01.ppo import (
    PPOConfig,
    PPOCounters,
    RecurrentPPOTrainer,
    config_digest,
    make_adam,
)


B1_RUN = "CBSC-OMRC-B1-THREE-SEED-SCOUT"


def test_literal_null_manifest_fields_preserve_every_deferred_value_as_none() -> None:
    packet = build_literal_null_manifest_fields()

    assert set(packet) == {"derived_fields", "auc_metadata", "diagnostic_metadata"}
    assert set(packet["derived_fields"]) == {
        "heldout_mean_return",
        "terminal_mean_return",
        "mean_oracle_regret",
        "normalized_return_auc",
        "struct_minus_raw_auc",
        "struct_minus_deranged_auc",
        "struct_minus_pi_auc",
        "oracle_action_accuracy",
        "invalid_serve_rate",
        "missed_serve_rate",
        "unnecessary_refresh_rate",
        "missed_refresh_rate",
        "inactive_fallback_accuracy",
        "owner_twin_flip_accuracy",
        "semantic_twin_flip_accuracy",
        "correct_swapped_sensitivity",
        "capability_specificity",
        "retention_gap_effect",
        "owner_event_order_effect",
        "semantic_event_order_effect",
        "clear_competent_null",
        "separation_from_deranged",
        "separation_from_pi",
        "residual_concentrated_in_gated",
        "material_instability",
        "adverse_seed",
        "catastrophic_seed",
        "promotion_eligible",
        "scientific_branch",
        "scientific_polarity",
        "b2_extension_trigger",
    }
    assert set(packet["auc_metadata"]) == {
        "return_auc_x_divisor",
        "return_auc_y_normalization",
        "return_auc_y_scale",
        "return_auc_split_scope",
        "return_auc_panel_pooling",
        "return_auc_episode_aggregation",
        "return_auc_seed_aggregation",
        "return_auc_pairing_rule",
        "return_auc_missing_rule",
        "return_auc_nonfinite_rule",
        "return_auc_scientific_interpretation",
    }
    assert set(packet["diagnostic_metadata"]) == {
        "oracle_action_accuracy",
        "invalid_serve_rate",
        "missed_serve_rate",
        "unnecessary_refresh_rate",
        "missed_refresh_rate",
        "inactive_fallback_accuracy",
        "owner_twin_flip_accuracy",
        "semantic_twin_flip_accuracy",
        "correct_swapped_sensitivity",
        "capability_specificity",
        "retention_gap_effect",
        "owner_event_order_effect",
        "semantic_event_order_effect",
    }
    expected_metadata = {
        "numerator",
        "denominator",
        "eligible_support_rule",
        "panel_scope",
        "split_pooling",
        "per_seed_aggregation",
        "checkpoint_reduction",
        "paired_unit",
        "minimum_support",
        "zero_denominator_rule",
        "effect",
        "interpretation",
    }
    assert all(value is None for value in packet["derived_fields"].values())
    assert all(value is None for value in packet["auc_metadata"].values())
    assert all(
        set(metadata) == expected_metadata
        and all(value is None for value in metadata.values())
        for metadata in packet["diagnostic_metadata"].values()
    )


def _exact(value: Fraction) -> dict[str, int]:
    return {"numerator": value.numerator, "denominator": value.denominator}


def _checkpoint_bytes(
    model: CommonRecurrentActorCritic, *, arm: str, update: int
) -> bytes:
    trainer = RecurrentPPOTrainer(
        model,
        run_name=B1_RUN,
        seed=model.seed,
        optimizer=make_adam(model),
        address_u64=addressing.u64,
    )
    trainer.counters = PPOCounters(
        rollout_updates=update,
        adam_steps=update * 16,
        train_episodes=update * 8,
        train_transitions=update * 8 * 152,
        train_decisions=update * 8 * 24,
    )
    binding = B1CheckpointBinding(
        object_id="CBSC-OMRC-B01",
        attempt_id="test-policy-records",
        run_name=B1_RUN,
        arm=arm,
        seed=model.seed,
        completed_rollout_updates=update,
        train_episode_ids_sha256="1" * 64,
        full_training_tape_digest="2" * 64,
        full_action_uniform_digest="3" * 64,
        ppo_configuration_digest=config_digest(PPOConfig()),
        implementation_commit="4" * 40,
        source_conformance_sha256="5" * 64,
    )
    envelope = capture_b1_checkpoint(trainer, binding)
    stream = io.BytesIO()
    torch.save(envelope, stream)
    return stream.getvalue()


def test_checkpoint_policy_records_replay_actual_model_adapter_and_ledger() -> None:
    seed = 21101
    host = DynamicHost(B1_RUN, seed)
    tapes = (
        host.build_stochastic(addressing.EVAL_STOCHASTIC, 1),
        host.build_stochastic(addressing.EVAL_STOCHASTIC, 0),
    )
    model = CommonRecurrentActorCritic(seed, address_u64=addressing.u64)
    checkpoint_bytes = _checkpoint_bytes(model, arm="RAW-GRU", update=0)

    rows = build_checkpoint_policy_records(
        run_name=B1_RUN,
        arm="RAW-GRU",
        seed=seed,
        checkpoint_update=0,
        checkpoint_bytes=checkpoint_bytes,
        tapes=tapes,
        model=model,
    )

    assert len(rows) == 48
    assert [
        (row["run_order"], row["seed"], row["checkpoint_update"],
         row["split_order"], row["tape_id"], row["opportunity_id"],
         row["arm_order"])
        for row in rows
    ] == sorted(
        (0, seed, 0, 1, tape_id, opportunity, 1)
        for tape_id in (0, 1)
        for opportunity in range(24)
    )
    first = rows[0]
    assert set(first) == {
        "run_order", "seed", "checkpoint_update", "split_order", "tape_id",
        "opportunity_id", "arm_order", "checkpoint_sha256", "parameter_sha256",
        "adapter_state_before_bytes", "adapter_state_after_bytes",
        "adapter_output_bytes", "legal_action_mask", "actor_logits_fp32_bits",
        "legal_action_probabilities_fp32_bits", "critic_value_fp32_bits",
        "selected_action", "selected_action_log_probability_fp32_bits",
        "observed_decision_reward", "observed_settlement_reward",
        "observed_opportunity_return", "hidden_state_before_sha256",
        "hidden_state_after_sha256",
    }
    assert first["checkpoint_sha256"] == hashlib.sha256(checkpoint_bytes).hexdigest()
    assert first["parameter_sha256"] == model_parameter_digest(model)
    assert first["legal_action_mask"] == [False, True, True, True]
    assert len(first["adapter_state_before_bytes"]) == 4
    assert len(first["adapter_state_after_bytes"]) == 4
    assert len(first["adapter_output_bytes"]) == 4
    assert len(first["actor_logits_fp32_bits"]) == 4
    assert len(first["legal_action_probabilities_fp32_bits"]) == 3
    assert 0 <= first["selected_action"] <= 2
    assert len(first["hidden_state_before_sha256"]) == 64
    assert len(first["hidden_state_after_sha256"]) == 64

    tape = host.build_stochastic(addressing.EVAL_STOCHASTIC, 0)
    action = Action(first["selected_action"] + 1)
    ledger = tape.evaluator().ledger(0, action)
    assert first["observed_decision_reward"] == _exact(ledger.decision_reward)
    assert first["observed_settlement_reward"] == _exact(ledger.settlement_reward)
    assert first["observed_opportunity_return"] == _exact(ledger.undiscounted_total)


def test_complete_policy_curves_publish_only_four_checkpoint_ledger_sums() -> None:
    seed = 21101
    host = DynamicHost(B1_RUN, seed)
    tapes = (
        host.build_stochastic(addressing.EVAL_STOCHASTIC, 0),
        host.build_motif(0),
    )
    model = CommonRecurrentActorCritic(seed, address_u64=addressing.u64)
    policy_rows = [
        row
        for update in (0, 12, 24, 48)
        for row in build_checkpoint_policy_records(
            run_name=B1_RUN,
            arm="STRUCT-CURRENTNESS-GRU",
            seed=seed,
            checkpoint_update=update,
            checkpoint_bytes=_checkpoint_bytes(
                model, arm="STRUCT-CURRENTNESS-GRU", update=update
            ),
            tapes=tapes,
            model=model,
        )
    ]

    curves = build_complete_policy_curves(policy_rows)

    assert len(curves) == 2
    assert [(row["split_order"], row["tape_id"]) for row in curves] == [(1, 0), (2, 0)]
    expected_fields = {
        "run_order", "seed", "split_order", "tape_id", "arm_order",
        "episode_return_update_0", "episode_return_update_12",
        "episode_return_update_24", "episode_return_update_48",
        "episode_decision_reward_sum_update_0",
        "episode_settlement_reward_sum_update_0",
        "episode_decision_reward_sum_update_12",
        "episode_settlement_reward_sum_update_12",
        "episode_decision_reward_sum_update_24",
        "episode_settlement_reward_sum_update_24",
        "episode_decision_reward_sum_update_48",
        "episode_settlement_reward_sum_update_48",
    }
    assert all(set(curve) == expected_fields for curve in curves)
    stochastic = curves[0]
    update_zero_rows = [
        row
        for row in policy_rows
        if row["checkpoint_update"] == 0 and row["split_order"] == 1
    ]
    direct = sum(
        (
            Fraction(item["observed_opportunity_return"]["numerator"],
                     item["observed_opportunity_return"]["denominator"])
            for item in update_zero_rows
        ),
        Fraction(0),
    )
    assert stochastic["episode_return_update_0"] == _exact(direct)
    assert stochastic["episode_return_update_0"] == stochastic["episode_return_update_48"]
    assert not any(
        forbidden in field
        for field in stochastic
        for forbidden in ("mean", "auc", "contrast", "interval", "sign")
    )


def test_policy_support_counts_join_truth_and_add_only_policy_coordinates() -> None:
    seed = 21101
    host = DynamicHost(B1_RUN, seed)
    tapes = (
        host.build_stochastic(addressing.EVAL_STOCHASTIC, 0),
        host.build_stochastic(addressing.EVAL_STOCHASTIC, 1),
    )
    model = CommonRecurrentActorCritic(seed, address_u64=addressing.u64)
    policy_rows = build_checkpoint_policy_records(
        run_name=B1_RUN,
        arm="PI-GRU",
        seed=seed,
        checkpoint_update=12,
        checkpoint_bytes=_checkpoint_bytes(model, arm="PI-GRU", update=12),
        tapes=tapes,
        model=model,
    )
    truth_rows = build_b1_shared_truth_tables(
        tapes,
        attempt_id="test-policy-records",
        literal_binding_spec_sha256="6" * 64,
    )["evaluator_decision_truth"]

    counts = build_policy_support_signature_counts(policy_rows, truth_rows)

    assert sum(row["support_count"] for row in counts) == 48
    assert all(row["arm_order"] == 2 and row["arm"] == "PI-GRU" for row in counts)
    assert all(row["checkpoint_update"] == 12 for row in counts)
    assert all(row["selected_action"] in (0, 1, 2) for row in counts)
    assert all(
        set(row)
        == {
            "run_order", "run_name", "seed", "split_order", "split", "motif_family_or_null",
            "motif_side_or_null", "request_active", "access_gated",
            "presented_body_native_neutral", "address_match_truth",
            "payload_source_match_truth", "content_match_truth", "owner_match_truth",
            "epoch_match_truth", "capability_match_truth", "overall_valid_truth",
            "oracle_action", "presented_body_age_opportunities", "arm_order", "arm",
            "checkpoint_update", "selected_action", "support_count",
        }
        for row in counts
    )


def test_checkpoint_policy_records_reject_model_not_restored_from_checkpoint_bytes() -> None:
    seed = 21101
    host = DynamicHost(B1_RUN, seed)
    model = CommonRecurrentActorCritic(seed, address_u64=addressing.u64)
    checkpoint_bytes = _checkpoint_bytes(model, arm="RAW-GRU", update=0)
    with torch.no_grad():
        model.actor_bias[1].add_(1.0)

    with pytest.raises(B1PolicyRecordError, match="checkpoint.*model"):
        build_checkpoint_policy_records(
            run_name=B1_RUN,
            arm="RAW-GRU",
            seed=seed,
            checkpoint_update=0,
            checkpoint_bytes=checkpoint_bytes,
            tapes=(host.build_stochastic(addressing.EVAL_STOCHASTIC, 0),),
            model=model,
        )
