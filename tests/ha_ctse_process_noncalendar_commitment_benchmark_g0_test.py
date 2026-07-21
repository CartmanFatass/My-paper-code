from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
import random

import numpy as np
import pytest
import torch

from ha_ctse_process.event_held_commitment_link import (
    CREATE,
    KEEP,
    RENEW,
    RNG_NAMES,
    authoritative_seed_map,
    collect_trajectory,
    compare_continuations,
    factor_counts,
    initialize_arms,
    load_checkpoint,
    make_training_state,
    nested_state_maximum_difference,
    optimize_update,
    parameter_and_optimizer_counts,
    runtime_rng_equal,
    runtime_rng_snapshot,
    save_checkpoint,
    validate_replay,
)
from ha_ctse_process.noncalendar_commitment_testbed import (
    ACCESS_FLOOR,
    EVENT_SEED,
    GAIN_THRESHOLD,
    HELD_OUT_EVAL_TASK_SEED,
    IID_EVAL_TASK_SEED,
    MARK_SEED,
    OPPORTUNITY_SEED,
    TRAIN_ACTION_SEED,
    TRAIN_ORDER_SEED,
    TRAIN_TASK_SEED,
    NoncalendarTrackingEnv,
    make_noncalendar_ledger,
    paired_ledgers_equal_except_targets,
    registered_contract,
    select_result_branch,
)
from scripts.run_noncalendar_commitment_benchmark_g0 import (
    ARMS,
    EVALUATION_CELLS,
    EVALUATION_CELL_SCHEMA,
    FORMAL_AUTHORIZATION,
    TRAIN_MANIFEST_SCHEMA,
    _evaluation_state,
    run_smoke,
    validate_operational_records,
)


@pytest.fixture(scope="module")
def cuda_device() -> torch.device:
    if not torch.cuda.is_available():
        pytest.fail(
            "EVENT_HELD_COMMITMENT_LINK_G0 focused evidence requires CUDA; "
            "no CPU fallback"
        )
    return torch.device("cuda")


def test_initialization_rng_isolation_and_capacity(
    cuda_device: torch.device,
) -> None:
    random.seed(144)
    np.random.seed(145)
    torch.manual_seed(146)
    torch.cuda.manual_seed_all(147)
    before = runtime_rng_snapshot()
    arms, base_optimizers, event_optimizers = initialize_arms(cuda_device)
    after = runtime_rng_snapshot()
    assert runtime_rng_equal(before, after)
    for name in ("base", "W_z", "event_head", "mark_head"):
        if name == "base":
            left = arms["DUM"].base.state_dict()
            right = arms["EHC"].base.state_dict()
        else:
            left = getattr(arms["DUM"], name).state_dict()
            right = getattr(arms["EHC"], name).state_dict()
        assert nested_state_maximum_difference(left, right) == 0.0
    changed, _, _ = initialize_arms(
        cuda_device, mark_seed=MARK_SEED + 1
    )
    assert nested_state_maximum_difference(
        arms["DUM"].W_z.state_dict(), changed["DUM"].W_z.state_dict()
    ) == 0.0
    assert nested_state_maximum_difference(
        arms["DUM"].event_head.state_dict(),
        changed["DUM"].event_head.state_dict(),
    ) == 0.0
    assert nested_state_maximum_difference(
        arms["DUM"].mark_head.state_dict(),
        changed["DUM"].mark_head.state_dict(),
    ) > 0.0
    dum_counts = parameter_and_optimizer_counts(
        arms["DUM"], base_optimizers["DUM"], event_optimizers["DUM"]
    )
    ehc_counts = parameter_and_optimizer_counts(
        arms["EHC"], base_optimizers["EHC"], event_optimizers["EHC"]
    )
    assert dum_counts == ehc_counts == {
        "base_model": 14980,
        "added_model": 1608,
        "base_optimizer": 15004,
        "event_optimizer": 1584,
    }


def test_ledger_rejoin_epoch_due_event_and_partial_continuity(
    cuda_device: torch.device,
) -> None:
    left = make_noncalendar_ledger(
        0, profile="held_out", task_seed=HELD_OUT_EVAL_TASK_SEED,
        order_seed=TRAIN_ORDER_SEED,
    )
    right = make_noncalendar_ledger(
        1, profile="held_out", task_seed=HELD_OUT_EVAL_TASK_SEED,
        order_seed=TRAIN_ORDER_SEED,
    )
    assert paired_ledgers_equal_except_targets(left, right)
    assert NoncalendarTrackingEnv(left).observe().observations.shape[1] == 15

    arms, _, _ = initialize_arms(cuda_device)
    full_state = make_training_state("EHC", 0)
    partial_state = make_training_state("EHC", 0)
    full = collect_trajectory(
        arms["EHC"], full_state, device=cuda_device, episode_ids=(0,)
    )
    first = collect_trajectory(
        arms["EHC"], partial_state, device=cuda_device,
        episode_ids=(0,), max_steps=17,
    )
    second = collect_trajectory(
        arms["EHC"], partial_state, device=cuda_device, cursor=first.cursor
    )
    for name in (
        "actions", "old_log_probs", "old_values", "hidden_after",
        "event_kind", "primitive_z", "event_z_pre",
    ):
        assert torch.equal(
            getattr(full, name),
            torch.cat((getattr(first, name), getattr(second, name))),
        )
    assert first.cutoff
    assert any(
        record.close_reason == "RENEW" and not record.censored
        for record in full.segments[0]
    )
    assert any(
        record.close_reason in ("TERMINAL_LEAVE", "EPISODE_END")
        and record.censored
        for record in full.segments[0]
    )

    forced_state = make_training_state("EHC", 0)
    pre_rejoin = collect_trajectory(
        arms["EHC"], forced_state, device=cuda_device,
        episode_ids=(0,), max_steps=40,
    )
    key = pre_rejoin.cursor.ledgers[0].temporary_key
    life = pre_rejoin.cursor.lifecycles[0][key]
    frozen_z = life.z.clone()
    frozen_hidden = pre_rejoin.cursor.hidden[0, key].clone()
    frozen_segment = life.segment_id
    frozen_start = life.segment_start_active_step
    old_epoch = life.membership_epoch
    life.q = 0
    rejoin = collect_trajectory(
        arms["EHC"], forced_state, device=cuda_device,
        cursor=pre_rejoin.cursor, max_steps=1,
    )
    event_kind = int(rejoin.event_kind[0, 0, key].detach().cpu())
    assert event_kind in (KEEP, RENEW)
    assert event_kind != CREATE
    assert torch.equal(rejoin.hidden_before[0, 0, key], frozen_hidden)
    assert torch.equal(rejoin.event_z_pre[0, 0, key], frozen_z)
    assert int(rejoin.membership_epoch[0, 0, key]) == old_epoch + 1
    restored = rejoin.cursor.lifecycles[0][key]
    assert restored.membership_epoch == old_epoch + 1
    if event_kind == KEEP:
        assert restored.segment_id == frozen_segment
        assert restored.segment_start_active_step == frozen_start
        assert torch.equal(rejoin.primitive_z[0, 0, key], frozen_z)
    else:
        assert restored.segment_id == frozen_segment + 1
        assert restored.segment_start_active_step == restored.active_steps - 1
        assert torch.equal(
            rejoin.primitive_z[0, 0, key],
            rejoin.event_new_z[0, 0, key],
        )


def _corrupt_tensor(tensor: torch.Tensor, index: tuple[int, ...]) -> torch.Tensor:
    value = tensor.clone()
    value[index] += 0.25
    return value


def test_semantic_replay_corruption_negatives(
    cuda_device: torch.device,
) -> None:
    arms, _, _ = initialize_arms(cuda_device)
    state = make_training_state("DUM", 0)
    trajectory = collect_trajectory(
        arms["DUM"], state, device=cuda_device, episode_ids=(0,)
    )
    _replay, errors = validate_replay(
        arms["DUM"], trajectory, device=cuda_device
    )
    assert max(errors.values()) <= 1e-6
    event_index = tuple(
        int(value) for value in torch.nonzero(
            trajectory.event_kind.ne(0), as_tuple=False
        )[0].detach().cpu()
    )
    mark_index = tuple(
        int(value) for value in torch.nonzero(
            trajectory.event_mark_mask, as_tuple=False
        )[0].detach().cpu()
    )
    prefix_index = (0, 0, 0, 0)

    corrupted = [
        replace(
            trajectory,
            event_inputs=_corrupt_tensor(
                trajectory.event_inputs, (*event_index, 0)
            ),
        ),
        replace(
            trajectory,
            event_cat_mask=trajectory.event_cat_mask.clone(),
        ),
        replace(
            trajectory,
            event_u=_corrupt_tensor(trajectory.event_u, (*mark_index, 0)),
        ),
        replace(
            trajectory,
            event_new_z=_corrupt_tensor(
                trajectory.event_new_z, (*mark_index, 0)
            ),
        ),
        replace(
            trajectory,
            prefix_counts=_corrupt_tensor(
                trajectory.prefix_counts, prefix_index
            ),
        ),
    ]
    corrupted[1].event_cat_mask[event_index] = ~corrupted[1].event_cat_mask[event_index]
    for value in corrupted:
        with pytest.raises(RuntimeError, match="semantic replay"):
            validate_replay(arms["DUM"], value, device=cuda_device)

    changed_kind = trajectory.event_kind.clone()
    changed_kind[event_index] = 0
    with pytest.raises(RuntimeError, match="semantic replay"):
        validate_replay(
            arms["DUM"], replace(trajectory, event_kind=changed_kind),
            device=cuda_device,
        )


def test_checkpoint_strict_continuation_and_cuda_smoke(
    cuda_device: torch.device, tmp_path,
) -> None:
    arms, base_optimizers, event_optimizers = initialize_arms(cuda_device)
    state = make_training_state("EHC", 0)
    trajectory = collect_trajectory(
        arms["EHC"], state, device=cuda_device, episode_ids=(0,)
    )
    update = optimize_update(
        arms["EHC"], base_optimizers["EHC"], event_optimizers["EHC"],
        state, trajectory, device=cuda_device,
    )
    assert update["primitive_replays"] == 4
    assert update["event_head_replays"] == 4
    assert update["packed_trajectory_count"] == 1
    checkpoint = tmp_path / "origin.pt"
    save_checkpoint(
        checkpoint, arm=arms["EHC"], base_optimizer=base_optimizers["EHC"],
        event_optimizer=event_optimizers["EHC"], state=state,
    )
    with pytest.raises(ValueError, match="arm/replicate"):
        load_checkpoint(
            checkpoint, device=cuda_device,
            expected_arm="DUM", expected_replicate=0,
        )
    with pytest.raises(ValueError, match="arm/replicate"):
        load_checkpoint(
            checkpoint, device=cuda_device,
            expected_arm="EHC", expected_replicate=1,
        )
    with pytest.raises(ValueError, match="update-250"):
        load_checkpoint(
            checkpoint, device=cuda_device,
            expected_arm="EHC", expected_replicate=0,
            formal_evaluation=True,
        )
    corrupt_payload = torch.load(checkpoint, map_location="cpu", weights_only=False)
    corrupt_payload["owned_rngs"].pop("mark")
    corrupt_path = tmp_path / "corrupt_rng.pt"
    torch.save(corrupt_payload, corrupt_path)
    with pytest.raises(ValueError, match="owned-RNG"):
        load_checkpoint(
            corrupt_path, device=cuda_device,
            expected_arm="EHC", expected_replicate=0,
        )

    left_arm, left_base, left_event, left_state = load_checkpoint(
        checkpoint, device=cuda_device,
        expected_arm="EHC", expected_replicate=0,
    )
    left_trajectory = collect_trajectory(
        left_arm, left_state, device=cuda_device, episode_ids=(1,)
    )
    optimize_update(
        left_arm, left_base, left_event, left_state,
        left_trajectory, device=cuda_device,
    )
    left_global = runtime_rng_snapshot()
    right_arm, right_base, right_event, right_state = load_checkpoint(
        checkpoint, device=cuda_device,
        expected_arm="EHC", expected_replicate=0,
    )
    right_trajectory = collect_trajectory(
        right_arm, right_state, device=cuda_device, episode_ids=(1,)
    )
    optimize_update(
        right_arm, right_base, right_event, right_state,
        right_trajectory, device=cuda_device,
    )
    right_global = runtime_rng_snapshot()
    continuation = compare_continuations(
        left_arm, right_arm, left_trajectory, right_trajectory,
        left_base, right_base, left_event, right_event,
        left_state, right_state, left_global, right_global,
    )
    assert continuation["discrete_equal"]
    assert continuation["lifecycle_equal"]
    assert continuation["owned_rng_equal"]
    assert continuation["global_rng_equal"]
    assert max(
        continuation[name] for name in (
            "continuous_error", "model_error", "base_optimizer_error",
            "event_optimizer_error",
        )
    ) <= 1e-7

    smoke = run_smoke(tmp_path / "smoke", device_name="cuda")
    assert smoke["device"] == "cuda" and smoke["formal"] is False
    assert smoke["or_dum_no_op"]
    assert all(value["update"]["primitive_replays"] == 4 for value in smoke["arms"].values())
    assert smoke["arms"]["DUM"]["update"]["base_zero_gradients"] == [1, 1, 1, 1]
    assert all(smoke["continuation"][name] for name in (
        "discrete_equal", "lifecycle_equal", "owned_rng_equal", "global_rng_equal"
    ))
    assert (tmp_path / "smoke" / "smoke_result.json").is_file()


def test_authoritative_seed_maps_and_independent_cells() -> None:
    training = authoritative_seed_map("train", 2)
    iid = authoritative_seed_map("iid", 2)
    held = authoritative_seed_map("held_out", 2)
    assert training == {
        "ledger": TRAIN_TASK_SEED + 2000,
        "order": TRAIN_ORDER_SEED + 2000,
        "primitive": TRAIN_ACTION_SEED + 2000,
        "opportunity": OPPORTUNITY_SEED + 2000,
        "event": EVENT_SEED + 2000,
        "mark": MARK_SEED + 2000,
    }
    assert iid == training | {"ledger": IID_EVAL_TASK_SEED + 2000}
    assert held == training | {"ledger": HELD_OUT_EVAL_TASK_SEED + 2000}
    all_seed_values = set(training.values()) | set(iid.values()) | set(held.values())
    assert 79_058 not in all_seed_values
    assert 89_058 not in all_seed_values
    states = [
        _evaluation_state("EHC", 2, profile=profile)
        for profile, _deterministic, _cell in EVALUATION_CELLS
    ]
    assert states[0] is not states[1] and states[2] is not states[3]
    assert states[0].seed_map == states[1].seed_map == iid
    assert states[2].seed_map == states[3].seed_map == held
    assert all(set(state.rngs) == set(RNG_NAMES) for state in states)


def _synthetic_operational_records() -> tuple[
    dict[str, object], dict[tuple[int, str, str], dict[str, object]]
]:
    contract = registered_contract()
    arms = {}
    for arm in ARMS:
        checkpoint = f"replicate_0/{arm}/update_250.pt"
        arms[arm] = {
            "arm": arm,
            "replicate": 0,
            "checkpoint": checkpoint,
            "checkpoint_origin": "update_250.pt",
            "completed_update": 250,
            "next_episode_id": 4000,
            "base_steps": 1000,
            "event_steps": 0 if arm == "OR" else 1000,
            "seed_map": authoritative_seed_map("train", 0),
            "checkpoint_resume": True,
        }
    training = {
        "schema_version": TRAIN_MANIFEST_SCHEMA,
        "contract": contract,
        "mode": "formal_train",
        "replicates": {
            "0": {
                "operational": {
                    "no_op": True,
                    "probability_replay": True,
                    "lifecycle": True,
                    "finiteness": True,
                    "rng_pairing": True,
                    "checkpoint_resume": True,
                    "exposure": True,
                },
                "updates": [{} for _ in range(250)],
                "arms": arms,
            }
        },
    }
    cells = {}
    episodes = [{"episode_id": value} for value in range(256)]
    for arm in ARMS:
        for profile, deterministic, cell in EVALUATION_CELLS:
            cells[(0, arm, cell)] = {
                "schema_version": EVALUATION_CELL_SCHEMA,
                "contract": contract,
                "arm": arm,
                "replicate": 0,
                "cell": cell,
                "profile": profile,
                "mode": "deterministic" if deterministic else "stochastic",
                "checkpoint": arms[arm]["checkpoint"],
                "checkpoint_origin": "update_250.pt",
                "counts": {"episodes": 256, "horizon": 80},
                "seed_map": authoritative_seed_map(profile, 0),
                "replay": {"maximum_error": 0.0},
                "operational": {
                    "probability_replay": True,
                    "lifecycle": True,
                    "rng": True,
                    "checkpoint": True,
                    "finite": True,
                },
                "episodes": deepcopy(episodes),
            }
    return training, cells


def test_fail_closed_operational_manifest_negatives() -> None:
    training, cells = _synthetic_operational_records()
    valid, errors = validate_operational_records(
        training, cells, expected_replicates=(0,)
    )
    assert valid and not errors
    corrupted_cell = deepcopy(cells)
    corrupted_cell[(0, "EHC", "iid_deterministic")]["profile"] = "held_out"
    assert not validate_operational_records(
        training, corrupted_cell, expected_replicates=(0,)
    )[0]
    for family, mutation in (
        ("no_op", lambda value: value["replicates"]["0"]["operational"].__setitem__("no_op", False)),
        ("exposure", lambda value: value["replicates"]["0"]["arms"]["EHC"].__setitem__("base_steps", 999)),
        ("resume", lambda value: value["replicates"]["0"]["arms"]["EHC"].__setitem__("checkpoint_resume", False)),
    ):
        corrupted = deepcopy(training)
        mutation(corrupted)
        operational_valid = validate_operational_records(
            corrupted, cells, expected_replicates=(0,)
        )[0]
        assert not operational_valid, family
        assert select_result_branch(
            **(_branch_inputs() | {"operational_valid": operational_valid})
        ) == "INVALID_OPERATIONAL"


def _branch_inputs() -> dict[str, object]:
    return {
        "operational_valid": True,
        "non_create_opportunities": 1000,
        "multi_opportunity_lifecycles": 250,
        "utility_ci": {
            "OR": (0.79, 0.81), "DUM": (0.79, 0.81), "EHC": (0.80, 0.84)
        },
        "g_ci": (0.11, 0.15),
        "keep_ci": (0.21, 0.30),
        "renew_ci": (0.11, 0.20),
        "cv_ci": (0.26, 0.35),
        "lifetime_bin_cis": ((0.11, 0.20), (0.11, 0.20), (0.05, 0.09)),
        "intervention_ci": (0.11, 0.20),
    }


def test_result_branch_first_match_and_boundaries() -> None:
    base = _branch_inputs()
    assert select_result_branch(**base) == "COMMITMENT_SUPPORTED"
    assert select_result_branch(
        **(base | {"operational_valid": False, "non_create_opportunities": 0})
    ) == "INVALID_OPERATIONAL"
    assert select_result_branch(
        **(base | {"non_create_opportunities": 999})
    ) == "BENCHMARK_NON_IDENTIFIABLE"
    low = {
        "OR": (0.1, ACCESS_FLOOR - 1e-6),
        "DUM": (0.1, 0.7),
        "EHC": (0.1, 0.7),
    }
    assert select_result_branch(
        **(base | {"utility_ci": low})
    ) == "NO_ACCESS_THIS_BENCHMARK"
    crossing = {
        "OR": (0.7, ACCESS_FLOOR),
        "DUM": (0.7, 0.8),
        "EHC": (0.7, 0.8),
    }
    assert select_result_branch(
        **(base | {"utility_ci": crossing})
    ) == "UNDERPOWERED_ACCESS"
    assert select_result_branch(
        **(base | {"keep_ci": (0.1, 0.20)})
    ) == "REPRESENTATION_ONLY"
    assert select_result_branch(
        **(base | {"g_ci": (0.0, GAIN_THRESHOLD)})
    ) == "ORDINARY_OR_CAPACITY_EXPLANATION_SUPPORTED"
    assert select_result_branch(
        **(base | {"g_ci": (0.05, 0.11), "keep_ci": (0.19, 0.21)})
    ) == "MIXED_UNDERPOWERED"
    contract = registered_contract()
    assert contract["arms"] == ["OR", "DUM", "EHC"]
    assert contract["duration_support"]["held_out"] == [5, 7, 9]
    assert contract["optimization"]["opportunity_support"] == [4, 8, 12]
