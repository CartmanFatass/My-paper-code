from copy import deepcopy

import pytest

from experiments.candidates.finite_resource_relational_inductive_efficiency.work import (
    AGGREGATED_WORK_SCHEMA,
    CHECKPOINT_CONVENTIONAL_FLOPS,
    CUMULATIVE_CHECKPOINT_SCHEMA,
    FINAL_CONVENTIONAL_FLOPS,
    FINAL_CUMULATIVE_SCHEMA,
    FLOP_ESTIMATOR_FORMULA,
    FLOP_ESTIMATOR_VERSION,
    FACTUAL_AUDIT_ENVIRONMENT_SLOTS,
    FACTUAL_AUDIT_FUTURE_ACTOR_STEPS,
    FACTUAL_AUDIT_FUTURE_POLICY_DECISIONS,
    FRRIE_ALL_24_BLOCK_TOTALS_V2,
    FRRIE_STATIC_FLOP_ESTIMATOR_V2,
    SHADOW_AUDIT_ACTOR_STEPS,
    SHADOW_AUDIT_ENVIRONMENT_SLOTS,
    aggregate_seed_blocks,
    checkpoint_cumulative_work,
    final_cumulative_work,
    planned_work,
    validate_cumulative_checkpoint_work,
)


@pytest.fixture
def compute():
    return {
        "device": "cpu",
        "model_dtype": "float32",
        "workers": 3,
        "threads": 2,
        "native_width": 8,
    }


def test_exact_logical_work_is_algebraic_per_arm_per_block(compute):
    work = planned_work(compute)
    assert work["PHY_TRUST"] == work["EDGE_FLEX"]
    row = work["PHY_TRUST"]
    assert row["accounting_basis"] == "PER_LEARNED_ARM_PER_SEED_BLOCK"
    assert row["seed_block_count"] == 24
    assert row["factual_train_environment_slots"] == 512 * 64 * 12 == 393_216
    assert row["factual_audits_per_episode"] == 3
    assert row["counterfactual_alternatives_per_episode"] == 7
    assert row["counterfactual_alternative_environment_slots"] == 1_490_944
    assert row["factual_audit_environment_slots"] == FACTUAL_AUDIT_ENVIRONMENT_SLOTS == 638_976
    assert row["alternative_suffix_environment_slots"] == 1_490_944 + 638_976 == 2_129_920
    assert row["learned_eval_environment_slots"] == 4 * 2 * 256 * 12 == 24_576
    assert row["environment_slots"] == 393_216 + 2_129_920 + 24_576 == 2_547_712
    assert SHADOW_AUDIT_ENVIRONMENT_SLOTS == 0
    assert SHADOW_AUDIT_ACTOR_STEPS == 2 * 256 * 12 == 6_144
    assert row["base_policy_decisions"] == 512 * 12 * (32 * 9 + 32 * 15) == 4_718_592
    assert row["counterfactual_alternative_future_actor_steps"] == 512 * 64 * 7 * 11 // 2 == 1_261_568
    assert row["counterfactual_alternative_future_policy_decisions"] == 15_138_816
    assert row["factual_audit_future_actor_steps"] == FACTUAL_AUDIT_FUTURE_ACTOR_STEPS == 540_672
    assert row["factual_audit_future_policy_decisions"] == FACTUAL_AUDIT_FUTURE_POLICY_DECISIONS == 6_488_064
    assert row["suffix_future_actor_steps"] == 1_261_568 + 540_672 == 1_802_240
    assert row["suffix_future_policy_decisions"] == 15_138_816 + 6_488_064 == 21_626_880
    assert row["learned_eval_policy_decisions"] == 256 * 12 * 2 * (9 + 15 + 6 + 21) == 313_344
    assert row["shadow_audit_policy_decisions"] == 256 * 12 * (6 + 21) == 82_944
    assert row["learned_decisions"] == 26_741_760
    assert row["backward_calls"] == row["adam_steps"] == 512
    assert row["parameter_bytes"] == 35_513 * 4 == 142_052
    assert row["checkpoint_io"] == 1
    assert row["evaluation_opportunities"] == 4 * 2 * 256 == 2_048
    # seed_block_count declares the panel; it does not silently multiply this
    # explicitly per-block vector.
    assert row["backward_calls"] != 512 * row["seed_block_count"]
    assert row["flops"] == FINAL_CONVENTIONAL_FLOPS == 1_979_786_229_248
    assert (row["workers"], row["threads"], row["native_width"], row["dtype"]) == (3, 2, 8, "float32")


def test_static_flop_estimator_recomputes_every_named_component():
    estimator = FRRIE_STATIC_FLOP_ESTIMATOR_V2
    assert estimator["schema"] == FLOP_ESTIMATOR_VERSION == "FRRIE_STATIC_FLOP_ESTIMATOR_V2"
    assert estimator["formula"] == FLOP_ESTIMATOR_FORMULA
    assert estimator["primitive_convention"]["backward_multiplier_of_factual_actor_plus_critic_forward"] == 2
    assert estimator["suffix_inventory"] == {
        "factual_audits_per_episode": 3,
        "counterfactual_alternatives_per_episode": 7,
        "counterfactual_alternative_environment_slots": 1_490_944,
        "counterfactual_alternative_future_actor_steps": 1_261_568,
        "counterfactual_alternative_future_policy_decisions": 15_138_816,
        "factual_audit_environment_slots": 638_976,
        "factual_audit_future_actor_steps": 540_672,
        "factual_audit_future_policy_decisions": 6_488_064,
        "all_suffix_future_actor_steps": 1_802_240,
        "all_suffix_future_policy_decisions": 21_626_880,
    }

    actor = estimator["actor_per_decision"]
    assert actor == {
        "multiplications": 26_892,
        "additions": 26_533,
        "bias_additions": 294,
        "nonlinearities": 294,
        "divisions": 7,
    }
    assert estimator["aggregation_per_actor_step"] == {
        "multiplications": 318,
        "additions": 243,
        "nonlinearities": 39,
        "divisions": 108,
    }
    actor_per_decision = sum(actor.values()) + 32
    actor_per_step = sum(estimator["aggregation_per_actor_step"].values())
    actor_forward = lambda decisions, steps: decisions * actor_per_decision + steps * actor_per_step

    factual_actor = actor_forward(4_718_592, 393_216)
    critic_role = 3 * 22 * 4_718_592 + 3 * 22 * (4_718_592 - 393_216) + 3 * 22 * 393_216
    critic_mlp = 393_216 * sum(estimator["critic_mlp_per_factual_slot"].values())
    factual_critic = critic_role + critic_mlp
    components = estimator["per_arm_per_seed_block_components"]
    assert components["factual_actor_forward"] == factual_actor
    assert components["factual_critic_forward"] == factual_critic
    assert components["factual_autograd_backward_convention"] == 2 * (factual_actor + factual_critic)
    assert components["counterfactual_alternative_actor_forward"] == actor_forward(15_138_816, 1_261_568)
    assert components["factual_audit_actor_forward"] == actor_forward(6_488_064, 540_672)
    assert components["learned_evaluation_actor_forward"] == actor_forward(313_344, 24_576)
    assert components["shadow_audit_actor_forward"] == actor_forward(82_944, SHADOW_AUDIT_ACTOR_STEPS)

    optimizer = estimator["optimizer_per_update"]
    assert components["gradient_norm_and_clip"] == 512 * optimizer["gradient_norm_and_clip"]
    assert components["adam"] == 512 * optimizer["adam"]
    assert components["beta_projection_bound_comparisons"] == 512 * 2 * 18
    assert FINAL_CONVENTIONAL_FLOPS == sum(components.values()) == 1_979_786_229_248
    assert CHECKPOINT_CONVENTIONAL_FLOPS == FINAL_CONVENTIONAL_FLOPS - components["learned_evaluation_actor_forward"] - components["shadow_audit_actor_forward"]
    assert CHECKPOINT_CONVENTIONAL_FLOPS == 1_958_344_320_512
    assert estimator["kind"].endswith("NOT_MEASURED_HARDWARE_FLOPS")
    assert "DATA_DEPENDENT_NATIVE_BRANCH_ARITHMETIC" in estimator["scope"]["excluded"]


def test_shadow_audit_is_symmetric_even_though_inference_uses_phy_v(compute):
    work = planned_work(compute)
    assert work["PHY_TRUST"]["shadow_audit_policy_decisions"] == 82_944
    assert work["EDGE_FLEX"]["shadow_audit_policy_decisions"] == 82_944
    assert work["PHY_TRUST"]["flops"] == work["EDGE_FLEX"]["flops"] == FINAL_CONVENTIONAL_FLOPS


def test_checkpoint_and_complete_panel_cumulative_split(compute):
    checkpoint = checkpoint_cumulative_work(compute)
    assert checkpoint["schema"] == CUMULATIVE_CHECKPOINT_SCHEMA
    assert checkpoint["training_update"] == 512
    assert checkpoint["evaluation_checkpoint_cursor"] == 0
    assert checkpoint["arms"]["PHY_TRUST"] == checkpoint["arms"]["EDGE_FLEX"]
    checkpoint_row = checkpoint["arms"]["PHY_TRUST"]
    assert checkpoint_row["learned_eval_environment_slots"] == 0
    assert checkpoint_row["learned_eval_policy_decisions"] == 0
    assert checkpoint_row["shadow_audit_policy_decisions"] == 0
    assert checkpoint_row["evaluation_opportunities"] == 0
    assert checkpoint_row["checkpoint_io"] == 1
    assert checkpoint_row["environment_slots"] == 393_216 + 2_129_920 == 2_523_136
    assert checkpoint_row["flops"] == CHECKPOINT_CONVENTIONAL_FLOPS
    assert validate_cumulative_checkpoint_work(checkpoint, compute) == checkpoint

    final = final_cumulative_work(compute)
    assert final["schema"] == FINAL_CUMULATIVE_SCHEMA
    assert final["training_update"] == 512
    assert final["evaluation_checkpoint_cursor"] == 1
    assert final["arms"] == planned_work(compute)
    assert final["arms"]["PHY_TRUST"]["evaluation_opportunities"] == 2_048
    assert final["arms"]["PHY_TRUST"]["flops"] == FINAL_CONVENTIONAL_FLOPS


def test_only_explicit_helper_aggregates_exactly_24_blocks(compute):
    per_block = planned_work(compute)
    aggregate = aggregate_seed_blocks(per_block)
    assert aggregate["schema"] == AGGREGATED_WORK_SCHEMA
    assert aggregate["seed_block_count"] == 24
    for arm in ("PHY_TRUST", "EDGE_FLEX"):
        assert aggregate["arms"][arm]["environment_slots"] == per_block[arm]["environment_slots"] * 24
        assert aggregate["arms"][arm]["learned_decisions"] == per_block[arm]["learned_decisions"] * 24
        assert aggregate["arms"][arm]["flops"] == per_block[arm]["flops"] * 24
        assert aggregate["arms"][arm]["workers"] == per_block[arm]["workers"]
        assert aggregate["arms"][arm]["seed_block_count"] == 24
        assert {
            field: aggregate["arms"][arm][field]
            for field in FRRIE_ALL_24_BLOCK_TOTALS_V2
        } == FRRIE_ALL_24_BLOCK_TOTALS_V2
    assert aggregate["arms"]["PHY_TRUST"]["backward_calls"] == 512 * 24 == 12_288
    assert aggregate["arms"]["PHY_TRUST"]["adam_steps"] == 512 * 24 == 12_288
    assert aggregate["arms"]["PHY_TRUST"]["evaluation_opportunities"] == 2_048 * 24 == 49_152
    assert aggregate["arms"]["PHY_TRUST"]["factual_audit_environment_slots"] == 638_976 * 24 == 15_335_424
    assert aggregate["arms"]["PHY_TRUST"]["factual_audit_future_actor_steps"] == 540_672 * 24 == 12_976_128
    assert aggregate["arms"]["PHY_TRUST"]["factual_audit_future_policy_decisions"] == 6_488_064 * 24 == 155_713_536
    assert aggregate["arms"]["PHY_TRUST"]["suffix_future_actor_steps"] == 1_802_240 * 24 == 43_253_760
    assert aggregate["arms"]["PHY_TRUST"]["environment_slots"] == 2_547_712 * 24 == 61_145_088
    assert aggregate["arms"]["PHY_TRUST"]["learned_decisions"] == 26_741_760 * 24 == 641_802_240
    assert aggregate["arms"]["PHY_TRUST"]["flops"] == 1_979_786_229_248 * 24 == 47_514_869_501_952
    with pytest.raises(ValueError, match="exactly 24"):
        aggregate_seed_blocks(per_block, 23)


@pytest.mark.parametrize("mutation", ["cursor", "evaluation", "flops", "arm_parity", "extra"])
def test_cumulative_checkpoint_mutation_is_rejected(compute, mutation):
    value = checkpoint_cumulative_work(compute)
    if mutation == "cursor":
        value["evaluation_checkpoint_cursor"] = 1
    elif mutation == "evaluation":
        value["arms"]["PHY_TRUST"]["evaluation_opportunities"] = 2_048
    elif mutation == "flops":
        value["arms"]["PHY_TRUST"]["flops"] += 1
    elif mutation == "arm_parity":
        value["arms"]["EDGE_FLEX"]["shadow_audit_policy_decisions"] = 82_944
    else:
        value["undeclared"] = True
    with pytest.raises(ValueError, match="differs"):
        validate_cumulative_checkpoint_work(value, compute)


def test_compute_binding_and_aggregate_mutation_rejection(compute):
    bad_compute = deepcopy(compute)
    bad_compute["native_width"] = False
    with pytest.raises(ValueError, match="native_width"):
        planned_work(bad_compute)
    bad_work = planned_work(compute)
    bad_work["EDGE_FLEX"]["learned_decisions"] += 1
    with pytest.raises(ValueError, match="symmetric"):
        aggregate_seed_blocks(bad_work)
