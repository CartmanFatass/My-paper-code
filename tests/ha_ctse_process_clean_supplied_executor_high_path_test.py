from __future__ import annotations

from copy import deepcopy

import numpy as np
import pytest
import torch

from ha_ctse_process.dynamic_roster_supplied_executor import (
    ACTION_SEED,
    BOOTSTRAP_REPETITIONS,
    BOOTSTRAP_SEED,
    EVALUATION_TASK_SEED,
    FORMAL_EVAL_EPISODES,
    FORMAL_HIGH_OPTIMIZER_STEPS,
    FORMAL_HORIZON,
    FORMAL_NUM_ENVS,
    FORMAL_TRANSITIONS,
    FORMAL_UPDATES,
    FRONTIER_STREAM_ID,
    HIGH_CHECKPOINT_SCHEMA_VERSION,
    LEARNED_HIGH_ARM,
    MODEL_SEED,
    OPPORTUNITY_FRONTIER_SEED,
    OPPORTUNITY_STREAM_ID,
    ORACLE_ARM,
    PPO_PASSES_PER_UPDATE,
    SuppliedExecutorVectorRuntime,
    SuppliedSkillExecutor,
    TRAIN_TASK_SEED,
    make_high_optimizer,
    make_model_owner,
    restore_high_only_checkpoint,
)
from ha_ctse_process.variable_roster_event import (
    SUPPLIED_EXECUTOR_RUNTIME,
    apply_event_ppo_update,
    batched_low_step,
    pack_event_ppo_data,
)
from scripts.run_clean_process_supplied_executor_high_path import (
    run_supplied_executor_qualification,
)


def test_clean_supplied_executor_high_path_g0_contract(tmp_path) -> None:
    executor = SuppliedSkillExecutor()
    numpy_before = np.random.get_state()
    torch_before = torch.get_rng_state().clone()
    assert executor({"a": 0, "b": 1, "c": 2}) == {
        "a": 0,
        "b": 1,
        "c": 2,
    }
    assert executor.parameter_count() == 0
    assert tuple(executor.parameters()) == ()
    assert all(
        np.array_equal(left, right)
        for left, right in zip(numpy_before, np.random.get_state())
    )
    assert torch.equal(torch_before, torch.get_rng_state())
    with pytest.raises(ValueError, match="outside"):
        executor({"a": 3})

    owner = make_model_owner("cpu")
    runtime = SuppliedExecutorVectorRuntime.create(
        arm=LEARNED_HIGH_ARM,
        model_owner=owner,
        episode_ids=(0,),
        task_seed=TRAIN_TASK_SEED,
        deterministic_high=False,
    )
    runtime.advance_one()
    core = runtime.cores[0]
    assert core.runtime_mode == SUPPLIED_EXECUTOR_RUNTIME
    assert core.low_hidden_dim == 0
    assert tuple(core.low_actor.parameters()) == ()
    assert tuple(core.low_critic.parameters()) == ()
    assert core.low_actor.state_dict() == {}
    assert core.low_critic.state_dict() == {}
    assert all(
        record.low_actor_hidden.size == 0
        and record.low_critic_hidden.size == 0
        for record in core.records.values()
    )
    assert not core.low_ledger
    assert not core.low_chunk_boundaries
    snapshot = runtime.current_transactions[0].pre_membership_boundary_snapshot
    with pytest.raises(RuntimeError, match="no-low-path"):
        core.low_step(snapshot)
    with pytest.raises(RuntimeError, match="no-low-path"):
        batched_low_step([core], [snapshot])
    with pytest.raises(RuntimeError, match=r"joint high\+low PPO"):
        pack_event_ppo_data([core])
    high_optimizer = make_high_optimizer(owner)
    with pytest.raises(RuntimeError, match=r"joint high\+low PPO"):
        apply_event_ppo_update(
            [core],
            high_optimizer=high_optimizer,
            low_optimizer=high_optimizer,
        )
    runtime.close()

    result = run_supplied_executor_qualification(
        output_root=tmp_path / "supplied-high-smoke",
        device_name="cpu",
        num_envs=1,
        updates=1,
        eval_episodes=2,
        smoke=True,
    )
    assert result["status"] == "SMOKE_COMPLETE"
    assert result["formal_evidence"] is False
    assert result["implementation_valid"] is True
    assert all(result["m0"].values()), result["m0"]
    assert all(result["carrier_audit"].values())
    counts = result["training"]["counts"]
    assert counts == {
        "environment_transitions": FORMAL_HORIZON,
        "high_optimizer_steps": PPO_PASSES_PER_UPDATE,
        "low_optimizer_steps": 0,
        "low_rows": 0,
        "low_likelihood_evaluations": 0,
        "episodes": 1,
    }
    assert max(result["training"]["first_pass_replay"].values()) <= 1.0e-6
    assert result["training"]["learned_high_drift"] > 0.0
    assert result["evaluation"]["frozen"]["high_tensor_drift"] == 0.0
    assert result["evaluation"]["oracle"]["high_tensor_drift"] == 0.0
    assert result["evaluation"]["frozen"]["optimizer_steps"] == 0
    assert result["evaluation"]["oracle"]["optimizer_steps"] == 0
    assert result["evaluation"]["learned"]["episode_ids"] == [0, 1]
    assert result["evaluation"]["frozen"]["episode_ids"] == [0, 1]
    assert result["evaluation"]["oracle"]["episode_ids"] == [0, 1]
    assert result["runner_selects_successor"] is False
    assert ORACLE_ARM == "routing_oracle"
    assert result["contract"]["arms"][-1] == "routing_oracle"

    formal = result["contract"]["formal"]
    assert formal == {
        "num_envs": FORMAL_NUM_ENVS,
        "horizon": FORMAL_HORIZON,
        "updates": FORMAL_UPDATES,
        "environment_transitions": FORMAL_TRANSITIONS,
        "ppo_passes_per_update": PPO_PASSES_PER_UPDATE,
        "high_optimizer_steps": FORMAL_HIGH_OPTIMIZER_STEPS,
        "low_optimizer_steps": 0,
        "evaluation_episodes_per_arm": FORMAL_EVAL_EPISODES,
        "training_episode_ids": [0, 3_999],
        "evaluation_episode_ids": [0, 255],
        "bootstrap_resamples": BOOTSTRAP_REPETITIONS,
    }
    assert result["contract"]["seed_contract"] == {
        "model": MODEL_SEED,
        "training_task": TRAIN_TASK_SEED,
        "opportunity_frontier": OPPORTUNITY_FRONTIER_SEED,
        "opportunity_stream": OPPORTUNITY_STREAM_ID,
        "frontier_stream": FRONTIER_STREAM_ID,
        "action": ACTION_SEED,
        "action_stream": 0,
        "evaluation_task": EVALUATION_TASK_SEED,
        "bootstrap": BOOTSTRAP_SEED,
    }
    assert BOOTSTRAP_REPETITIONS == 10_000
    checkpoint = torch.load(
        result["checkpoint_path"], map_location="cpu", weights_only=False
    )
    assert checkpoint["checkpoint_schema_version"] == HIGH_CHECKPOINT_SCHEMA_VERSION
    assert checkpoint["runtime_mode"] == SUPPLIED_EXECUTOR_RUNTIME
    assert checkpoint["arm"] == LEARNED_HIGH_ARM
    assert checkpoint["counters"]["environment_transitions"] == FORMAL_HORIZON
    assert checkpoint["counters"]["high_optimizer_steps"] == (
        PPO_PASSES_PER_UPDATE
    )
    optimizer_state = checkpoint["optimizer_state"]
    assert len(optimizer_state["state"]) == len(
        tuple(owner.commitment_model.parameters())
        + tuple(owner.event_critic.parameters())
    )
    assert all(
        set(state) == {"step", "exp_avg", "exp_avg_sq"}
        for state in optimizer_state["state"].values()
    )

    restore_owner = make_model_owner("cpu")
    restore_runtime = SuppliedExecutorVectorRuntime.create(
        arm=LEARNED_HIGH_ARM,
        model_owner=restore_owner,
        episode_ids=(0,),
        task_seed=TRAIN_TASK_SEED,
        deterministic_high=False,
    )
    restore_optimizer = make_high_optimizer(restore_owner)
    incomplete_optimizer = deepcopy(checkpoint)
    incomplete_optimizer["optimizer_state"]["state"].pop(
        next(iter(incomplete_optimizer["optimizer_state"]["state"]))
    )
    with pytest.raises(ValueError, match="incomplete"):
        restore_high_only_checkpoint(
            incomplete_optimizer,
            restore_runtime,
            optimizer=restore_optimizer,
        )
    changed_hyperparameter = deepcopy(checkpoint)
    changed_hyperparameter["optimizer_state"]["param_groups"][0]["betas"] = (
        0.8,
        0.999,
    )
    with pytest.raises(ValueError, match="hyperparameter"):
        restore_high_only_checkpoint(
            changed_hyperparameter,
            restore_runtime,
            optimizer=restore_optimizer,
        )
    noncanonical_owner = make_model_owner("cpu")
    noncanonical_runtime = SuppliedExecutorVectorRuntime.create(
        arm=LEARNED_HIGH_ARM,
        model_owner=noncanonical_owner,
        episode_ids=(1,),
        task_seed=TRAIN_TASK_SEED,
        deterministic_high=False,
    )
    with pytest.raises(ValueError, match="counter-canonical"):
        restore_high_only_checkpoint(
            checkpoint,
            noncanonical_runtime,
            optimizer=make_high_optimizer(noncanonical_owner),
        )
    restore_runtime.close()
    noncanonical_runtime.close()

    dry = run_supplied_executor_qualification(
        output_root=tmp_path / "supplied-high-dry",
        device_name="cpu",
        num_envs=1,
        updates=1,
        eval_episodes=2,
        smoke=True,
        dry_validate=True,
    )
    assert dry["status"] == "DRY_VALID"
    assert dry["formal_contract"]["low_optimizer_steps"] == 0
    assert (
        tmp_path
        / "supplied-high-smoke"
        / "checkpoints"
        / "update_000_high.pt"
    ).is_file()
    assert (
        tmp_path
        / "supplied-high-smoke"
        / "result"
        / "clean_supplied_executor_high_path_g0.json"
    ).is_file()
    assert (tmp_path / "supplied-high-smoke" / "runner_status.txt").is_file()
