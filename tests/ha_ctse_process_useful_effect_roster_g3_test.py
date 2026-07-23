from __future__ import annotations

from pathlib import Path
from collections import Counter

import pytest
import torch

from ha_ctse_process.useful_effect_roster_g3 import (
    ARM_NAMES,
    PASS_SOURCE_CONTROL,
    SeedRegistry,
    collect_arm_batch,
    evaluate_source_controls,
    initialize_matched_arms,
    load_arm_checkpoint,
    make_deficit_mates,
    make_episode_spec,
    optimize_arm_batch,
    pack_specs,
    replay_errors,
    save_arm_checkpoint,
)


def test_paired_source_uses_demand_served_not_label_diversity() -> None:
    controls = evaluate_source_controls()
    assert controls["result"] == PASS_SOURCE_CONTROL
    assert controls["constructive_oracle_utility"] == 1.0
    assert controls["duplicate_demand_present"] is True
    assert controls["zero_demand_label_present"] is True
    assert controls["all_source_checks"] is True

    for profile in (
        "train",
        "iid",
        "heldout_cardinality",
        "heldout_gap",
        "heldout_joint",
    ):
        for base_id in range(48):
            spec = make_episode_spec(profile, base_id=base_id)
            assert sum(spec.demand) == spec.active_count
            assert len([value for value in spec.demand if value > 0]) >= 2
            standing = spec.standing_counts
            assert standing[spec.deficit] + 1 == spec.demand[spec.deficit]
            assert all(
                standing[index] == spec.demand[index]
                for index in range(4)
                if index != spec.deficit
            )
            assert spec.utility(spec.deficit) == 1.0
            assert spec.utility((spec.deficit + 1) % 4) <= 1.0
            assert len(spec.query) == 13
            assert len(spec.critic) == 17
            assert all(len(token) == 7 for token in spec.roster_tokens)
            assert all(len(token) == 10 for token in spec.history_tokens)


def test_deficit_mates_hide_optimal_effect_from_base_query() -> None:
    mates = make_deficit_mates("heldout_joint", base_id=91)
    assert len(mates) >= 2
    assert len({spec.demand for spec in mates}) == 1
    assert len({spec.deficit for spec in mates}) == len(mates)
    assert len({spec.query for spec in mates}) == 1
    assert len({spec.standing_counts for spec in mates}) == len(mates)


def test_sequential_ledgers_balance_every_demand_deficit_event_cell() -> None:
    for profile in (
        "iid",
        "heldout_cardinality",
        "heldout_gap",
        "heldout_joint",
    ):
        cells = Counter(
            (spec.demand, spec.deficit, spec.event_kind)
            for spec in (
                make_episode_spec(profile, base_id=2_000_000_000 + index)
                for index in range(512)
            )
        )
        assert min(cells.values()) >= 1
        assert max(cells.values()) - min(cells.values()) <= 1


def test_roster_attention_is_token_order_invariant() -> None:
    specs = [make_episode_spec("heldout_joint", base_id=value) for value in range(8)]
    packed = pack_specs(specs)
    state = initialize_matched_arms(
        replicate=0,
        source_commit="1" * 40,
        seed_registry=SeedRegistry(),
    )["ROSTER_ATTN"]
    with torch.no_grad():
        original = state.model.edit_logits("ROSTER_ATTN", packed)
        reversed_packed = packed.with_reversed_roster_tokens()
        reversed_logits = state.model.edit_logits("ROSTER_ATTN", reversed_packed)
    torch.testing.assert_close(original, reversed_logits, rtol=0, atol=1e-7)


@pytest.mark.parametrize("arm", ARM_NAMES)
def test_replay_ppo_and_gradient_fences(arm: str) -> None:
    specs = [make_episode_spec("train", base_id=value) for value in range(64)]
    packed = pack_specs(specs)
    state = initialize_matched_arms(
        replicate=1,
        source_commit="2" * 40,
        seed_registry=SeedRegistry(),
    )[arm]
    batch = collect_arm_batch(state, packed)
    errors = replay_errors(state.model, batch)
    assert errors["logp"] <= 1e-7
    assert errors["value"] <= 1e-7
    metrics = optimize_arm_batch(state, batch, passes=1)
    assert metrics["optimizer_steps"] == 1
    assert metrics["maximum_forbidden_gradient"] == 0.0
    assert metrics["maximum_gradient"] > 0.0


def test_checkpoint_restores_optimizer_rng_and_rejects_foreign_source(
    tmp_path: Path,
) -> None:
    source_commit = "3" * 40
    specs = [make_episode_spec("train", base_id=value) for value in range(32)]
    state = initialize_matched_arms(
        replicate=2,
        source_commit=source_commit,
        seed_registry=SeedRegistry(),
    )["TEAM_REC"]
    batch = collect_arm_batch(state, pack_specs(specs))
    optimize_arm_batch(state, batch, passes=1)
    checkpoint = tmp_path / "team.pt"
    save_arm_checkpoint(checkpoint, state)

    restored = initialize_matched_arms(
        replicate=2,
        source_commit=source_commit,
        seed_registry=SeedRegistry(),
    )["TEAM_REC"]
    load_arm_checkpoint(checkpoint, restored, source_commit=source_commit)
    assert restored.completed_updates == state.completed_updates
    assert restored.optimizer_steps == state.optimizer_steps
    for key, value in state.model.state_dict().items():
        torch.testing.assert_close(value, restored.model.state_dict()[key])
    torch.testing.assert_close(
        state.action_generator.get_state(), restored.action_generator.get_state()
    )

    with pytest.raises(ValueError, match="source commit"):
        load_arm_checkpoint(checkpoint, restored, source_commit="4" * 40)
