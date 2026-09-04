from __future__ import annotations

import copy

import pytest
import torch

torch.set_num_threads(1)

from experiments.candidates.eociv_lite import one_step_root_partition_frozen_history as b7


def test_registered_literals_and_full_counts_are_exact() -> None:
    assert b7.HISTORY_SEEDS == {"H0": 91031, "H1": 91032, "H2": 91033}
    assert b7.HISTORY_ACTION_TAPES == {"H0": 91101, "H1": 91102, "H2": 91103}
    assert b7.HISTORY_ORDER_TAPES == {"H0": 91201, "H1": 91202, "H2": 91203}
    assert b7.PREFIX_ROOTS == tuple(range(910101, 910109))
    assert b7.SHOCK_TUPLES == (("A", "A"), ("A", "B"), ("B", "A"), ("B", "B"))
    assert b7.PROFILE_NAMES == (
        "train_4_3_6_5",
        "train_5_3_7_6",
        "train_6_4_8_6",
    )
    assert b7.FULL_PLAN.expected_counts == b7.FULL_EXPECTED_COUNTS
    assert b7.FULL_EXPECTED_COUNTS["unique_complete_episodes"] == 918
    assert b7.FULL_EXPECTED_COUNTS["environment_transitions"] == 44_064
    assert b7.FULL_EXPECTED_COUNTS["prefix_episodes"] == 288
    assert b7.FULL_EXPECTED_COUNTS["common_data_collection_episodes"] == 144
    assert b7.FULL_EXPECTED_COUNTS["evaluation_episodes"] == 486
    assert b7.FULL_EXPECTED_COUNTS["physical_trajectory_references"] == 288
    assert b7.FULL_EXPECTED_COUNTS["learner_batch_episode_references"] == 576
    assert b7.FULL_EXPECTED_COUNTS["learner_calls"] == 144
    assert b7.FULL_EXPECTED_COUNTS["optimizer_updates"] == 144


def test_panel_and_evaluation_literal_tables_are_complete_disjoint_and_exact() -> None:
    expected_keys = {
        (history, profile) for history in b7.HISTORY_IDS for profile in b7.PROFILE_NAMES
    }
    assert set(b7.PANEL_ROOTS) == expected_keys
    assert set(b7.PANEL_ACTION_TAPES) == expected_keys
    assert set(b7.EVALUATION_ROOTS) == expected_keys
    panel_roots = [root for values in b7.PANEL_ROOTS.values() for root in values]
    evaluation_roots = [root for values in b7.EVALUATION_ROOTS.values() for root in values]
    assert len(panel_roots) == len(set(panel_roots)) == 36
    assert len(evaluation_roots) == len(set(evaluation_roots)) == 27
    assert not set(panel_roots) & set(evaluation_roots)
    assert not set(panel_roots) & set(b7.PREFIX_ROOTS)
    assert not set(evaluation_roots) & set(b7.PREFIX_ROOTS)
    assert b7.PANEL_ROOTS[("H0", "train_4_3_6_5")] == (920101, 920102, 920103, 920104)
    assert b7.PANEL_ACTION_TAPES[("H2", "train_6_4_8_6")] == 942121
    assert b7.EVALUATION_ROOTS[("H2", "train_6_4_8_6")] == (932121, 932122, 932123)


def test_clustered_and_latin_partitions_are_distinct_exact_covers() -> None:
    witness = b7.partition_witness()
    assert witness["clustered_rows"] == [
        [0, 1, 2, 3], [4, 5, 6, 7], [8, 9, 10, 11], [12, 13, 14, 15]
    ]
    assert witness["latin_rows"] == [
        [0, 5, 10, 15], [4, 9, 14, 3], [8, 13, 2, 7], [12, 1, 6, 11]
    ]
    assert all(
        witness[key]
        for key in (
            "clustered_exact_cover",
            "latin_exact_cover",
            "same_information_multiset",
            "four_episodes_per_branch",
        )
    )
    assert witness["clustered_rows"] != witness["latin_rows"]


def test_branch_precedence_is_exact_on_hand_checkable_aggregates() -> None:
    base = {
        "grand": {
            "J": 1.0, "C": 0.0, "G": 0.0,
            "correct_improvement": 1.0, "swapped_improvement": 0.0,
        },
        "by_history": {history: {"J": 1.0} for history in b7.HISTORY_IDS},
        "leave_one_profile": {profile: {"J": 1.0} for profile in b7.PROFILE_NAMES},
        "leave_one_root_index": {str(index): {"J": 1.0} for index in range(3)},
        "R_by_history": {history: 1.0 for history in b7.HISTORY_IDS},
    }
    assert b7.select_terminal_branch(base, fidelity_valid=False) == "B7_INVALID_OR_UNIDENTIFIED"
    assert b7.select_terminal_branch(base, fidelity_valid=True) == "B7_ROOT_SEMANTIC_EDGE"

    generic = copy.deepcopy(base)
    generic["grand"].update(J=-1.0, C=1.0, G=0.5, swapped_improvement=1.0)
    generic["by_history"] = {history: {"J": -1.0} for history in b7.HISTORY_IDS}
    assert b7.select_terminal_branch(generic, fidelity_valid=True) == "B7_GENERIC_OPTIMIZATION_ONLY"

    null = copy.deepcopy(base)
    null["grand"].update(J=-1.0, C=-1.0, G=-1.0, correct_improvement=-1.0)
    null["by_history"] = {history: {"J": -1.0} for history in b7.HISTORY_IDS}
    assert b7.select_terminal_branch(null, fidelity_valid=True) == "B7_ROOT_LOCAL_NULL"

    moderated = copy.deepcopy(null)
    moderated["by_history"]["H0"] = {"J": 1.0}
    assert b7.select_terminal_branch(moderated, fidelity_valid=True) == "B7_HISTORY_MODERATED_OR_JOINT"


def test_actor_optimizer_clone_preserves_order_state_and_digest() -> None:
    actor, optimizer = b7._new_actor_optimizer()
    state = copy.deepcopy(actor.state_dict())
    optimizer_state = copy.deepcopy(optimizer.state_dict())
    clone, clone_optimizer = b7._new_actor_optimizer(state, optimizer_state)
    assert list(actor.state_dict()) == list(clone.state_dict())
    assert b7._state_dict_digest(actor.state_dict()) == b7._state_dict_digest(clone.state_dict())
    assert b7._optimizer_digest(optimizer.state_dict()) == b7._optimizer_digest(clone_optimizer.state_dict())
    manifest = b7._structural_manifest(actor, optimizer)
    assert manifest["optimizer_parameter_groups"][0]["parameter_names"] == [
        name for name, _ in actor.named_parameters()
    ]
    assert manifest["gradient_rule"] == "actor_mean_plus_half_scaled_critic_mean"
    assert manifest["clip_rule"] == "JOINT_GLOBAL_CLIP"
    assert manifest["clip_cap"] == pytest.approx(0.5)


def test_configuration_freezes_normalized_terminal_gae_adam_and_firewalls() -> None:
    configuration = b7.registered_configuration()
    assert configuration["horizon"] == 48
    assert configuration["gamma"] == pytest.approx(0.99)
    assert configuration["gae_lambda"] == pytest.approx(0.95)
    assert configuration["adam_lr"] == pytest.approx(3e-4)
    assert configuration["global_clip_cap"] == pytest.approx(0.5)
    assert configuration["evaluation_arms"] == ["CORRECT", "SWAPPED"]
    assert "actor/critic replay channels" in configuration["learner_batch_episode_reference_rule"]
    assert b7.FULL_EXPECTED_COUNTS["retry"] == 0
    assert b7.FULL_EXPECTED_COUNTS["rescue"] == 0
    assert b7.FULL_EXPECTED_COUNTS["sweep"] == 0
    assert b7.FULL_EXPECTED_COUNTS["checkpoint_selection"] == 0
