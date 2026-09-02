from __future__ import annotations

import dataclasses

import pytest
import torch

from experiments.candidates.scdmp_variable_k.multifoundation_reachable_order_value import contracts
from experiments.candidates.scdmp_variable_k.multifoundation_reachable_order_value.foundation import (
    CompetenceRecord,
    FoundationActorCritic,
    FoundationContractError,
    analyze_competence,
    classify_ordered_branch,
    direct_tensor_state,
    materialize_foundation,
)
from experiments.candidates.scdmp_variable_k.multifoundation_reachable_order_value.rng import (
    CounterRNG,
    RNGContractError,
)
from experiments.candidates.scdmp_variable_k.multifoundation_reachable_order_value.training import (
    ExactAdamW,
    RolloutBatch,
    TrainingContractError,
    make_final_checkpoint,
    restore_final_checkpoint,
    duration_correct_gae,
    build_training_plan,
    train_one_update,
)


def test_manifest_is_the_frozen_b01_static_and_run_contract() -> None:
    manifest = contracts.Manifest()
    run_manifest = contracts.build_run_manifest(b"scdmp-b01-test-master-32-bytes!!")

    assert manifest.schema == contracts.NAMED_RUN_ID
    assert contracts.TRAINING_SEEDS == (1709, 2903)
    assert contracts.K_VALUES == (7, 13)
    assert contracts.FOUNDATION_UPDATES == 160
    assert contracts.EPISODES_PER_UPDATE == 12
    assert contracts.ADAMW_STEPS_PER_FOUNDATION == 1_920
    assert contracts.CURVE_UPDATES == (0, 20, 40, 60, 80, 100, 120, 140, 160)
    assert contracts.CURVE_MISSIONS_PER_CELL == 8
    assert contracts.COMPETENCE_MISSIONS_PER_CELL == 32
    assert tuple((state.k, state.stratum, state.target_tick, state.source_seed) for state in contracts.STATE_SPECS) == (
        (7, "early", 64, 1709),
        (7, "middle", 160, 2903),
        (7, "late", 256, 1709),
        (13, "early", 64, 2903),
        (13, "middle", 160, 1709),
        (13, "late", 256, 2903),
    )
    assert len({state.cell for state in contracts.STATE_SPECS}) == 6
    assert len(contracts.ACTION_TABLE) == 18
    assert contracts.ACTION_TABLE[0] == (1, (0, 0, 0, 0))
    assert contracts.ACTION_TABLE[-1] == (2, (0, -1, 0, 1))
    assert contracts.DEVELOPMENT_TAPES == tuple(range(8))
    assert contracts.HELDOUT_TAPES == tuple(range(16))
    assert contracts.ORDERED_BRANCHES == (
        "INVALID_OR_INCOMPLETE_ATTEMPT",
        "FOUNDATION_COMPETENCE_NOT_ESTABLISHED",
        "REACHABLE_STATE_PANEL_NOT_ESTABLISHED",
        "ACTION_CONSTRUCTION_NONDISCRIMINATING",
        "PRELIMINARY_REPEATABLE_ORDER_VALUE_SIGNAL",
        "GENERIC_ACTION_OR_RECOVERY_EXPLANATION",
        "ORDER_ASSOCIATION_NOT_OBSERVED_IN_RUN_01",
        "FOUNDATION_STATE_OR_SELECTOR_HETEROGENEITY",
    )
    assert contracts.RESOURCE_CAPS == {
        "peak_rss_bytes": 2_147_483_648,
        "scratch_bytes": 268_435_456,
        "durable_bytes": 268_435_456,
        "wall_seconds": 1_800,
    }
    assert contracts.WORKLOADS["training_episodes_per_foundation"] == 1_920
    assert contracts.WORKLOADS["adamw_steps_per_foundation"] == 1_920
    assert contracts.WORKLOADS["development_graph_action_mission_cells"] == 3_456
    assert contracts.WORKLOADS["heldout_matched_swapped_common_mission_cells"] == 1_152
    assert contracts.WORKLOADS["total_missions_rollouts"] == 9_328
    assert run_manifest.q_by_cell in contracts.Q_PATTERNS
    assert sum(run_manifest.q_by_cell) == 3
    assert all(
        {run_manifest.q_by_cell[left], run_manifest.q_by_cell[right]} == {0, 1}
        for left, right in ((0, 3), (1, 4), (2, 5))
    )
    assert run_manifest.q_pattern_index == run_manifest.q_counter_u64 % 4
    assert run_manifest.pre_event_p == (1, 2, 3, 4)
    assert run_manifest.hr_post_pq == ((4, 2, 1, 3), 1)
    assert run_manifest.rh_post_pq == ((1, 4, 2, 3), 0)
    assert run_manifest.to_dict()["q_by_cell"] == list(run_manifest.q_by_cell)
    assert contracts.build_run_manifest(b"scdmp-b01-test-master-32-bytes!!") == run_manifest

    manifest.validate()
    encoded = manifest.to_dict()
    assert encoded["training_seeds"] == [1709, 2903]
    assert encoded["resource_caps"] == contracts.RESOURCE_CAPS

    with pytest.raises(contracts.ContractError):
        dataclasses.replace(manifest, foundation_updates=159).validate()
    with pytest.raises(contracts.ContractError):
        contracts.build_run_manifest(b"short")


def test_counter_rng_is_addressed_domain_separated_and_seed_bound() -> None:
    left = CounterRNG(1709)
    same = CounterRNG(1709)
    other_seed = CounterRNG(2903)
    address = ("actor.layers.0.weight", 17)

    expected = left.uniform53("foundation-initialization", address)
    # Unrelated draws cannot move an addressed stream.
    left.uniform53("training-categorical", (4, 9, 2))
    assert left.uniform53("foundation-initialization", address) == expected
    assert same.uniform53("foundation-initialization", address) == expected
    assert left.uniform53("foundation-initialization", ("actor.layers.0.weight", 18)) != expected
    assert left.uniform53("foundation-training", address) != expected
    assert other_seed.uniform53("foundation-initialization", address) != expected

    assert sorted(left.permutation(31, domain="foundation-minibatch", address=(7, 2))) == list(range(31))
    assert left.permutation(31, domain="foundation-minibatch", address=(7, 2)) == same.permutation(
        31, domain="foundation-minibatch", address=(7, 2)
    )

    with pytest.raises(RNGContractError):
        CounterRNG(1710)
    with pytest.raises(RNGContractError):
        left.uniform53("", address)
    with pytest.raises(RNGContractError):
        left.uniform53("foundation-initialization", (True,))


def test_foundations_are_real_float32_actor_critics_and_seed_independent() -> None:
    first = materialize_foundation(CounterRNG(1709))
    replay = materialize_foundation(CounterRNG(1709))
    second = materialize_foundation(CounterRNG(2903))

    assert isinstance(first, FoundationActorCritic)
    assert sum(parameter.numel() for parameter in first.parameters()) == 24_115
    assert all(parameter.dtype == torch.float32 for parameter in first.parameters())
    assert direct_tensor_state(first) == direct_tensor_state(replay)
    assert direct_tensor_state(first) != direct_tensor_state(second)

    observation = torch.zeros((5, 18), dtype=torch.float32)
    output = first(observation)
    assert output.logits.shape == (5, 18)
    assert output.value.shape == (5,)
    assert output.logits.dtype == output.value.dtype == torch.float32
    assert torch.isfinite(output.logits).all()
    assert torch.isfinite(output.value).all()


def test_training_plan_balances_three_complete_episodes_per_graph_k_cell() -> None:
    plan = build_training_plan()
    assert len(plan) == 1_920
    assert plan[0].update == 1
    assert plan[-1].update == 160
    for update in (1, 79, 160):
        rows = tuple(row for row in plan if row.update == update)
        assert len(rows) == 12
        assert {
            (graph, k): sum(row.graph == graph and row.k == k for row in rows)
            for graph in ("HR", "RH")
            for k in (7, 13)
        } == {("HR", 7): 3, ("RH", 7): 3, ("HR", 13): 3, ("RH", 13): 3}


def test_duration_correct_gae_uses_primitive_duration_in_bootstrap_and_trace() -> None:
    targets = duration_correct_gae(
        ((1.0, 2.0), (3.0,)),
        torch.tensor((0.5, 0.25), dtype=torch.float32),
        torch.tensor((True, False), dtype=torch.bool),
        episode_offsets=(0, 2),
    )

    assert targets.discounted_rewards.tolist() == pytest.approx((2.99, 3.0), abs=2e-6)
    assert targets.deltas.tolist() == pytest.approx((2.73750625, 2.75), abs=2e-6)
    assert targets.raw_advantages.tolist() == pytest.approx((5.092255961875001, 2.75), abs=2e-6)
    assert targets.value_targets.tolist() == pytest.approx((5.592255961875001, 3.0), abs=2e-6)
    assert float(targets.normalized_advantages.mean()) == pytest.approx(0.0, abs=2e-6)


def test_real_ppo_adamw_update_changes_float32_foundation_on_bounded_batch() -> None:
    model = materialize_foundation(CounterRNG(1709))
    optimizer = ExactAdamW(tuple(model.named_parameters()))
    observations = torch.linspace(-0.2, 0.3, 12 * 18, dtype=torch.float32).reshape(12, 18)
    actions = torch.arange(12, dtype=torch.int64)
    with torch.no_grad():
        output = model(observations)
        old_log_probabilities = torch.log_softmax(output.logits, dim=1).gather(
            1, actions[:, None]
        ).squeeze(1)
        old_values = output.value.detach().clone()
    batch = RolloutBatch(
        observations=observations,
        actions=actions,
        old_log_probabilities=old_log_probabilities,
        old_values=old_values,
        primitive_rewards=tuple((float(index) / 11.0,) for index in range(12)),
        nonterminal=torch.zeros(12, dtype=torch.bool),
        episode_offsets=tuple(range(13)),
        episode_slots=build_training_plan()[:12],
    )
    before = direct_tensor_state(model)

    receipt = train_one_update(model, optimizer, CounterRNG(1709), batch, update=1)

    assert receipt.update == 1
    assert receipt.episodes_complete == 12
    assert receipt.records == 12
    assert receipt.optimizer_step == 12
    assert receipt.transitions == 12
    assert direct_tensor_state(model) != before
    assert all(torch.isfinite(parameter).all() for parameter in model.parameters())

    wrong_seed_model = materialize_foundation(CounterRNG(2903))
    wrong_seed_optimizer = ExactAdamW(tuple(wrong_seed_model.named_parameters()))
    with pytest.raises(TrainingContractError, match="seed-bound"):
        train_one_update(
            wrong_seed_model, wrong_seed_optimizer, CounterRNG(1709), batch, update=1,
        )

    with pytest.raises(TrainingContractError, match="graph-by-k"):
        graph_drift_model = materialize_foundation(CounterRNG(1709))
        train_one_update(
            graph_drift_model,
            ExactAdamW(tuple(graph_drift_model.named_parameters())),
            CounterRNG(1709),
            dataclasses.replace(batch, episode_slots=tuple(reversed(batch.episode_slots))),
            update=1,
        )


def test_update_160_checkpoint_is_direct_and_independent_after_restore() -> None:
    source = materialize_foundation(CounterRNG(1709))
    source_optimizer = ExactAdamW(tuple(source.named_parameters()))
    source_optimizer.restore(dataclasses.replace(source_optimizer.snapshot(), step=1_920))

    with pytest.raises(TrainingContractError):
        make_final_checkpoint(source, source_optimizer, update=159)
    checkpoint = make_final_checkpoint(source, source_optimizer, update=160)

    restored = materialize_foundation(CounterRNG(2903))
    restored_optimizer = ExactAdamW(tuple(restored.named_parameters()))
    restore_final_checkpoint(
        restored,
        restored_optimizer,
        checkpoint,
        expected_seed=1709,
    )
    assert direct_tensor_state(restored) == direct_tensor_state(source)
    assert restored.foundation_seed == 1709
    assert restored_optimizer.snapshot().step == 1_920
    assert all(
        torch.equal(left, right)
        for left, right in zip(
            restored_optimizer.snapshot().first,
            source_optimizer.snapshot().first,
        )
    )

    checkpoint_first_bytes = checkpoint.parameters[0].tensor.numpy().tobytes()
    with torch.no_grad():
        next(source.parameters()).add_(1.0)
    assert direct_tensor_state(restored) != direct_tensor_state(source)
    assert checkpoint.parameters[0].tensor.numpy().tobytes() == checkpoint_first_bytes


def _competence_records(*, weak_first_cell: bool = False) -> tuple[CompetenceRecord, ...]:
    records = []
    for seed in contracts.TRAINING_SEEDS:
        for graph in contracts.GRAPHS:
            for k in contracts.K_VALUES:
                successes = 23 if weak_first_cell and (seed, graph, k) == (1709, "HR", 7) else 28
                for mission in range(32):
                    records.append(CompetenceRecord(
                        seed=seed,
                        graph=graph,
                        k=k,
                        mission=mission,
                        terminal=True,
                        finite=True,
                        evaluator_valid=True,
                        safe_dock=mission < successes,
                        failures=(),
                    ))
    return tuple(records)


def test_competence_requires_exact_32_per_cell_and_all_frozen_counts() -> None:
    passed = analyze_competence(_competence_records())
    assert passed.complete
    assert passed.passed
    assert tuple(row.safe_docks for row in passed.cells) == (28,) * 8
    assert all(row.passed for row in passed.foundations)

    failed = analyze_competence(_competence_records(weak_first_cell=True))
    assert failed.complete
    assert not failed.passed
    assert not next(row for row in failed.foundations if row.seed == 1709).passed

    with pytest.raises(FoundationContractError):
        analyze_competence(_competence_records()[:-1])


def test_generic_branch_classifier_uses_exact_pro_order() -> None:
    flags = {name: False for name in contracts.ORDERED_BRANCHES}
    flags["PRELIMINARY_REPEATABLE_ORDER_VALUE_SIGNAL"] = True
    flags["FOUNDATION_STATE_OR_SELECTOR_HETEROGENEITY"] = True
    assert classify_ordered_branch(flags) == "PRELIMINARY_REPEATABLE_ORDER_VALUE_SIGNAL"

    flags["FOUNDATION_COMPETENCE_NOT_ESTABLISHED"] = True
    assert classify_ordered_branch(flags) == "FOUNDATION_COMPETENCE_NOT_ESTABLISHED"

    with pytest.raises(FoundationContractError):
        classify_ordered_branch({"NOT_A_PRO_BRANCH": True})
