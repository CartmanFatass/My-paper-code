from __future__ import annotations

from copy import deepcopy
from types import SimpleNamespace

import numpy as np
import pytest
import torch

from ha_ctse_process.dynamic_roster_spatial_testbed import (
    HORIZON,
    LEFT,
    RIGHT,
    STAY,
    SpatialDynamicRosterEventEnv,
    constructive_spatial_actions,
    make_spatial_dynamic_roster_ledger,
)
from ha_ctse_process.process_semantics import (
    ConditionalProcessPosterior,
    ProcessSemanticTrainer,
    ProcessWindowLedger,
    restore_event_semantic_bundle,
    snapshot_event_semantic_bundle,
)
from ha_ctse_process.dynamic_roster_direct import (
    DirectPrimitiveARPolicy,
    evaluate_direct_policy,
)
from ha_ctse_process.dynamic_roster_spatial_testbed import (
    make_spatial_environment,
)
from ha_ctse_process.variable_roster_event import (
    EventTransactionResult,
    LowTransitionRow,
    event_action_hooks,
    lifecycle_boundary_hooks,
    low_row_index_hooks,
)
from ha_ctse_process.train import (
    enforce_iteration5_process_semantics_contract,
    is_iteration5_process_semantics,
)
from scripts.run_iteration5_process_semantics import (
    _load_hierarchical_owner,
    _matched_shuffle_residual_ci,
    _select_reference_pair,
    _semantic_materiality_audit,
    run_iteration5,
)


def _assert_nested_equal(left, right) -> None:
    if isinstance(left, np.ndarray) or isinstance(right, np.ndarray):
        assert np.array_equal(np.asarray(left), np.asarray(right))
    elif hasattr(left, "__dataclass_fields__") or hasattr(right, "__dataclass_fields__"):
        assert type(left) is type(right)
        for name in left.__dataclass_fields__:
            _assert_nested_equal(getattr(left, name), getattr(right, name))
    elif isinstance(left, dict) and isinstance(right, dict):
        assert left.keys() == right.keys()
        for key in left:
            _assert_nested_equal(left[key], right[key])
    elif isinstance(left, (list, tuple)) and isinstance(right, (list, tuple)):
        assert len(left) == len(right)
        for lhs, rhs in zip(left, right):
            _assert_nested_equal(lhs, rhs)
    else:
        assert left == right


def _low_row(key: str, epoch: int, skill: int, reward: float = 0.0) -> LowTransitionRow:
    return LowTransitionRow(
        lifecycle_key=key,
        membership_epoch=epoch,
        policy_version=0,
        physical_time=0,
        observation=np.zeros(15, dtype=np.float32),
        skill=skill,
        action=np.asarray([STAY], dtype=np.int64),
        old_log_probability=0.0,
        old_value=0.0,
        actor_hidden_before=np.zeros(4, dtype=np.float32),
        critic_hidden_before=np.zeros(4, dtype=np.float32),
        critic_member_features=np.zeros(15, dtype=np.float32),
        active_critic_member_features=np.zeros((1, 15), dtype=np.float32),
        active_skills=np.asarray([skill], dtype=np.int64),
        critic_global_features=np.zeros(8, dtype=np.float32),
        focal_active_index=0,
        critic_source_summary=np.zeros(4, dtype=np.float32),
        reward=float(reward),
    )


def test_spatial_carrier_membership_process_view_and_snapshot_round_trip() -> None:
    ledger = make_spatial_dynamic_roster_ledger(7)
    env = SpatialDynamicRosterEventEnv(task_master_seed=ledger.master_seed)
    transaction = env.reset_event_runtime(ledger.episode_id)
    assert set(transaction.post_membership_pre_policy_snapshot.keys) == {"0", "1", "2", "3"}
    assert env.process_state_mapping((0, 1, 2, 3)) == {
        "0": 0.0,
        "1": 0.5,
        "2": 0.5,
        "3": 0.5,
    }
    first_member = next(
        member
        for member in transaction.post_membership_pre_policy_snapshot.members
        if member.lifecycle_key == "0"
    )
    assert first_member.observation.shape == (15,)
    assert first_member.observation[11] == 0.0
    assert np.array_equal(first_member.observation[12:15], [0.0, 1.0, 0.0])

    for _ in range(20):
        view = env.environment.observe()
        actions = {str(key): STAY for key in view.active_keys}
        env.step_event_runtime(actions)
    leave = env.environment.event_transaction()
    left = tuple(str(key) for key in ledger.temporary_leave)
    assert tuple(delta.lifecycle_key for delta in leave.atomic_membership_delta) == left
    frozen = env.process_state_mapping(left)
    snapshot = env.snapshot_event_runtime()

    restored = SpatialDynamicRosterEventEnv(task_master_seed=1)
    restored.restore_event_runtime(deepcopy(snapshot))
    assert restored.process_state_mapping(left) == frozen
    _assert_nested_equal(restored.snapshot_event_runtime(), snapshot)


def test_constructive_spatial_controller_reaches_registered_carrier_bounds() -> None:
    outcomes = []
    for episode_id in range(8):
        env = SpatialDynamicRosterEventEnv(task_master_seed=57_057)
        env.reset_event_runtime(episode_id)
        for _ in range(HORIZON):
            view = env.environment.observe()
            env.step_event_runtime(
                {
                    str(key): action
                    for key, action in constructive_spatial_actions(
                        env.environment, view
                    ).items()
                }
            )
        outcomes.append(env.environment.outcome())
    assert min(outcome.persistent_score for outcome in outcomes) >= 0.95
    assert min(outcome.short_score for outcome in outcomes) >= 0.95
    assert min(outcome.utility for outcome in outcomes) >= 0.95


def test_process_window_ownership_scores_and_low_reward_assignment() -> None:
    ledger = ProcessWindowLedger(max_window_length=12)
    ledger.open_window(
        lifecycle_key="0",
        membership_epoch=0,
        policy_version=0,
        skill=1,
        start_observation=np.zeros(15, dtype=np.float32),
        start_actor_hidden=np.zeros(4, dtype=np.float32),
        start_process_state=0.0,
    )
    ledger.observe_transition(
        lifecycle_key="0",
        membership_epoch=0,
        policy_version=0,
        low_row_index=0,
        post_process_state=0.5,
    )
    ledger.apply_event_boundary(
        lifecycle_key="0",
        membership_epoch=0,
        policy_version=0,
        action_kind="KEEP",
        next_skill=1,
        observation=np.ones(15, dtype=np.float32),
        actor_hidden=np.ones(4, dtype=np.float32),
        process_state=0.5,
    )
    ledger.observe_transition(
        lifecycle_key="0",
        membership_epoch=0,
        policy_version=0,
        low_row_index=1,
        post_process_state=1.0,
    )
    ledger.apply_event_boundary(
        lifecycle_key="0",
        membership_epoch=0,
        policy_version=0,
        action_kind="SET",
        next_skill=2,
        observation=np.ones(15, dtype=np.float32),
        actor_hidden=np.ones(4, dtype=np.float32),
        process_state=1.0,
    )
    ledger.close_rollout()
    windows = ledger.closed_windows
    assert len(windows) == 2
    assert windows[0].linked_low_row_indices == (0, 1)
    assert windows[0].process_state_sequence == (0.0, 0.5, 1.0)
    assert windows[1].valid_length == 0

    posterior = ConditionalProcessPosterior(
        observation_dim=15,
        actor_hidden_dim=4,
        n_skills=3,
        hidden_dim=8,
    )
    trainer = ProcessSemanticTrainer(posterior, beta=0.05, device="cpu")
    trainer.semantic_ready = True
    trainer.frozen.load_state_dict(trainer.online.state_dict())
    rows = [_low_row("0", 0, 1), _low_row("0", 0, 1)]
    scores = trainer.score_closed_windows(windows)
    applied = trainer.apply_low_rewards(rows, windows, scores)
    assert applied == 2
    assert sum(float(row.reward) for row in rows) == pytest.approx(
        0.05 * scores[0]
    )

    off_rows = [_low_row("0", 0, 1), _low_row("0", 0, 1)]
    off = ProcessSemanticTrainer(
        ConditionalProcessPosterior(15, 4, 3, 8), beta=0.0, device="cpu"
    )
    off.semantic_ready = True
    off.frozen.load_state_dict(off.online.state_dict())
    assert off.apply_low_rewards(off_rows, windows, off.score_closed_windows(windows)) == 0
    assert [row.reward for row in off_rows] == [0.0, 0.0]


def test_posterior_gradient_isolation_and_semantic_checkpoint_round_trip() -> None:
    torch.manual_seed(3)
    posterior = ConditionalProcessPosterior(15, 4, 3, 8)
    trainer = ProcessSemanticTrainer(posterior, beta=0.05, device="cpu", sampler_seed=11)
    ledger = ProcessWindowLedger(max_window_length=12)
    for skill, length in ((0, 2), (1, 3), (2, 4)):
        ledger.open_window(
            lifecycle_key=str(skill),
            membership_epoch=0,
            policy_version=0,
            skill=skill,
            start_observation=np.full(15, skill, dtype=np.float32),
            start_actor_hidden=np.full(4, skill, dtype=np.float32),
            start_process_state=0.0,
        )
        for index in range(length):
            ledger.observe_transition(
                lifecycle_key=str(skill),
                membership_epoch=0,
                policy_version=0,
                low_row_index=skill * 10 + index,
                post_process_state=float(index + 1) / 4.0,
            )
        ledger.close_window(str(skill), 0, 0)

    external = torch.nn.Parameter(torch.tensor(2.0))
    metrics = trainer.update_posterior(ledger.closed_windows)
    assert metrics["posterior_steps"] == 1.0
    assert external.grad is None
    assert trainer.semantic_ready

    bundle = snapshot_event_semantic_bundle(
        trainer=trainer,
        ledgers=[ledger],
        intrinsic_applied_count=5,
    )
    clone = ProcessSemanticTrainer(
        ConditionalProcessPosterior(15, 4, 3, 8), beta=0.05, device="cpu", sampler_seed=99
    )
    clone_ledger = ProcessWindowLedger(max_window_length=12)
    restored_count = restore_event_semantic_bundle(
        bundle,
        trainer=clone,
        ledgers=[clone_ledger],
    )
    assert restored_count == 5
    assert clone.semantic_ready
    assert clone_ledger.state_dict() == ledger.state_dict()
    for name, value in trainer.online.state_dict().items():
        assert torch.equal(value, clone.online.state_dict()[name])
    with pytest.raises(ValueError, match="semantic bundle"):
        restore_event_semantic_bundle({}, trainer=clone, ledgers=[clone_ledger])


def test_event_runtime_exposes_stable_semantic_hooks() -> None:
    assert callable(event_action_hooks)
    assert callable(lifecycle_boundary_hooks)
    assert callable(low_row_index_hooks)
    assert EventTransactionResult.__annotations__["token_rows"]


def test_direct_control_reuses_same_spatial_carrier_without_model_change() -> None:
    model = DirectPrimitiveARPolicy(hidden_dim=8)
    result = evaluate_direct_policy(
        model,
        episode_ids=[0],
        deterministic=True,
        device=torch.device("cpu"),
        ledger_factory=make_spatial_dynamic_roster_ledger,
        environment_factory=make_spatial_environment,
    )
    assert len(result["utility"]) == 1
    assert np.isfinite(result["utility"]).all()


def test_iteration5_dispatch_is_distinct_and_fails_closed() -> None:
    config = SimpleNamespace(
        high_controller="variable_roster_event",
        event_architecture_mode="f0",
        iteration5_process_semantics_arm="c1_semantic_on",
    )
    args = SimpleNamespace(
        r28_g1_arm="off",
        r29_action_info_mode="off",
        r31_effect_mode="off",
    )
    assert is_iteration5_process_semantics(config)
    enforce_iteration5_process_semantics_contract(config, args)
    with pytest.raises(ValueError, match="semantic bundle"):
        enforce_iteration5_process_semantics_contract(
            config, args, {"has_event_semantic": False}
        )

    config.event_architecture_mode = "f1"
    with pytest.raises(ValueError, match="exact F0"):
        enforce_iteration5_process_semantics_contract(config, args)

    config.iteration5_process_semantics_arm = ""
    with pytest.raises(ValueError, match="non-Iteration-5"):
        enforce_iteration5_process_semantics_contract(
            config, args, {"has_event_semantic": True}
        )


def test_iteration5_reference_selection_and_matched_shuffle_are_frozen() -> None:
    reference = np.zeros((64, 3, 2, 2), dtype=np.float64)
    reference[:, 0, :, 0] = -1.0
    reference[:, 1, :, 0] = 1.0
    selected, energies = _select_reference_pair(reference)
    assert selected == (0, 1)
    assert energies[(0, 1)] > energies[(0, 2)]
    assert energies[(0, 1)] > energies[(1, 2)]

    centroids = np.asarray([[-1.0, 0.0], [1.0, 0.0], [0.0, 0.0]])
    labels = np.tile(np.asarray([0, 1], dtype=np.int64), 8)
    natural = centroids[labels].copy()
    masks = np.full(labels.shape, 4, dtype=np.int64)
    starts = np.repeat(np.arange(8, dtype=np.float64), 2)
    residual_ci, supported = _matched_shuffle_residual_ci(
        natural=natural,
        centroids=centroids,
        labels=labels,
        masks=masks,
        starts=starts,
        pair=selected,
        repetitions=1_000,
    )
    assert supported
    assert residual_ci[0] > 0.0


@pytest.mark.skipif(not torch.cuda.is_available(), reason="Iteration-5 smoke requires CUDA")
def test_iteration5_exact_runner_tiny_smoke(tmp_path) -> None:
    result = run_iteration5(
        output_root=tmp_path / "iteration5_smoke",
        smoke=True,
        num_envs=2,
        updates=1,
        eval_episodes=2,
    )
    assert result["status"] == "SMOKE_COMPLETE"
    assert result["implementation_valid"]
    on = result["arms"]["c1_semantic_on"]
    off = result["arms"]["c1_semantic_off"]
    assert on["zero"] == off["zero"]
    assert on["m0"]["strict_semantic_checkpoint_round_trip"]
    assert off["m0"]["strict_semantic_checkpoint_round_trip"]
    assert max(on["replay"].values()) <= 1e-6
    assert max(off["replay"].values()) <= 1e-6
    assert result["semantic_audit"] is None
    owner = _load_hierarchical_owner(
        tmp_path
        / "iteration5_smoke"
        / "c1_semantic_on"
        / "checkpoints"
        / "latest.pt",
        torch.device("cuda"),
    )
    audit = _semantic_materiality_audit(
        owner,
        on["final"]["stochastic"]["natural_skill_step_shares"],
        smoke=True,
    )
    assert not audit["scientific"]
    assert audit["source_count"] == 2
    assert audit["effect_shape"] == [2, 3, 2, 2]
    assert set(audit["pairs"]) == {"0-1", "0-2", "1-2"}
