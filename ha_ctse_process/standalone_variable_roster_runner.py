"""Variable-roster Stage-C production runner."""

from __future__ import annotations

import argparse
import csv
from copy import deepcopy
import json
from pathlib import Path
import time
from typing import Any, Mapping, Sequence

import numpy as np
import torch

from ha_ctse_process.env_factory import normalize_scenario
from ha_ctse_process.standalone_cli import create_collector
from ha_ctse_process.standalone_event_support import (
    _evaluate_event_model,
    _event_identity_normalizers,
    _event_live_checkpoint_paths,
    _event_state_dict_finite,
    _make_event_model_owner,
    _make_event_runtime,
    _nested_state_maximum_difference,
    _paired_mean_ci,
    _summarize_event_prefix_rows,
    _write_event_arm_status,
    _write_event_csv_rows,
    _write_event_json,
    enforce_variable_roster_event_resume_boundary,
)
from ha_ctse_process.standalone_metrics import emit


def run_variable_roster_event_branch(config, args: argparse.Namespace, writer):
    """Run one exact Stage-C arm, including fresh zero/final evidence."""

    from ha_ctse_process.collectors import SyncEnvCollector
    from ha_ctse_process.dynamic_roster_testbed import (
        DynamicRosterEventEnv,
        HORIZON,
        TRAIN_LEDGER_SEED,
    )
    from ha_ctse_process.variable_roster_event import (
        EVENT_ARCHITECTURE_SCHEMA_VERSION,
        apply_event_ppo_update,
        batched_low_step,
        event_model_only_checkpoint_payload,
        pack_event_ppo_data,
        restore_event_model_only_checkpoint,
        restore_vector_event_checkpoint,
        vector_event_checkpoint_payload,
    )

    enforce_variable_roster_event_resume_boundary(config, args)
    if normalize_scenario(str(getattr(config, "scenario", ""))) != (
        "generic_short_dynamic_roster"
    ):
        raise ValueError("variable_roster_event is restricted to generic-SHORT Stage C")
    num_envs = int(args.num_envs)
    if (num_envs, int(args.rollout_length), int(args.total_timesteps)) != (
        16,
        HORIZON,
        320_000,
    ):
        raise ValueError(
            "Stage C requires num_envs=16, rollout_length=80, total_timesteps=320000"
        )
    if int(getattr(config, "event_architecture_schema_version", -1)) != (
        EVENT_ARCHITECTURE_SCHEMA_VERSION
    ):
        raise ValueError("Stage C requires event architecture schema version 1")
    if str(getattr(args, "device", "cuda")).lower() != "cuda" or not torch.cuda.is_available():
        raise RuntimeError("Stage C training requires available CUDA; CPU fallback is forbidden")
    device = torch.device("cuda")
    config.dynamic_roster_task_ledger_seed = TRAIN_LEDGER_SEED
    output_root = Path(args.log_dir)
    checkpoint_dir = output_root / "checkpoints"
    evaluation_dir = output_root / "evaluation"
    result_dir = output_root / "result"
    for directory in (checkpoint_dir, evaluation_dir, result_dir):
        directory.mkdir(parents=True, exist_ok=True)

    with torch.random.fork_rng(devices=[torch.cuda.current_device()]):
        torch.manual_seed(57_057)
        torch.cuda.manual_seed_all(57_057)
        model_owner = _make_event_model_owner(config, device)
    high_optimizer = torch.optim.Adam(
        tuple(model_owner.commitment_model.parameters())
        + tuple(model_owner.event_critic.parameters()),
        lr=3e-4,
    )
    low_optimizer = torch.optim.Adam(
        tuple(model_owner.low_actor.parameters())
        + tuple(model_owner.low_critic.parameters()),
        lr=3e-4,
    )
    normalizer_states = _event_identity_normalizers()

    def model_state(core) -> dict[str, Any]:
        return {
            "commitment_model": deepcopy(core.commitment_model.state_dict()),
            "event_critic": deepcopy(core.event_critic.state_dict()),
            "low_actor": deepcopy(core.low_actor.state_dict()),
            "low_critic": deepcopy(core.low_critic.state_dict()),
        }

    zero_checkpoint_path = checkpoint_dir / "update_000_eval.pt"
    zero_evaluation_path = evaluation_dir / "update_000.json"
    if not str(getattr(args, "resume_from", "") or ""):
        torch.save(
            event_model_only_checkpoint_payload(
                model_owner=model_owner,
                normalizer_states=normalizer_states,
                total_steps=0,
                update_idx=0,
            ),
            zero_checkpoint_path,
        )
        zero_owner = _make_event_model_owner(config, device)
        restore_event_model_only_checkpoint(
            torch.load(zero_checkpoint_path, map_location=device, weights_only=False),
            model_owner=zero_owner,
        )
        initial_state = model_state(zero_owner)
        _write_event_arm_status(
            args,
            state="running",
            phase="zero_evaluation",
            mode=config.event_architecture_mode,
            update=0,
            updates_total=250,
            steps=0,
            steps_total=320_000,
            high_optimizer_steps=0,
            low_optimizer_steps=0,
            optimizer_steps_total=1_000,
        )
        zero_evaluation = {
            "deterministic": _evaluate_event_model(
                zero_owner,
                deterministic=True,
                capture_prefix=False,
                capture_forced_audit=False,
            ),
            "stochastic": _evaluate_event_model(
                zero_owner,
                deterministic=False,
                capture_prefix=False,
                capture_forced_audit=False,
            ),
        }
        _write_event_json(zero_evaluation_path, zero_evaluation)
    else:
        if not zero_checkpoint_path.is_file() or not zero_evaluation_path.is_file():
            raise FileNotFoundError(
                "Stage C resume requires the original zero checkpoint and evaluation"
            )
        zero_payload = torch.load(
            zero_checkpoint_path, map_location=device, weights_only=False
        )
        zero_owner = _make_event_model_owner(config, device)
        restore_event_model_only_checkpoint(zero_payload, model_owner=zero_owner)
        initial_state = model_state(zero_owner)
        zero_evaluation = json.loads(zero_evaluation_path.read_text(encoding="utf-8"))

    collector = create_collector(config, args, scale_mode="train", num_envs=num_envs)
    collector.event_runtime_capability()
    total_steps = 0
    update_idx = 0
    high_optimizer_steps = 0
    low_optimizer_steps = 0
    intrinsic_applied_count = 0
    next_episode_id = 0
    resumed_from = None
    maximum_replay_errors = {
        "high_logp_max_error": 0.0,
        "high_value_max_error": 0.0,
        "low_logp_max_error": 0.0,
        "low_value_max_error": 0.0,
    }
    finite_updates = True
    last_metrics: dict[str, float] = {}
    update_path = output_root / "train_updates.csv"
    latest_checkpoint_path = checkpoint_dir / "latest.pt"
    update_fields = [
        "update",
        "steps",
        "high_optimizer_steps",
        "low_optimizer_steps",
        *maximum_replay_errors,
        "high_loss",
        "low_loss",
        "finite_update",
    ]

    def prepare_episode_batch(episode_ids: Sequence[int]):
        transactions = collector.reset_event_runtime(episode_ids)
        prepared_cores = []
        prepared_snapshots = []
        for env_index, (episode_id, transaction) in enumerate(
            zip(episode_ids, transactions)
        ):
            core = _make_event_runtime(
                model_owner,
                environment_index=env_index,
                episode_id=int(episode_id),
                event_master_seed=77_057,
                action_master_seed=87_057,
            )
            bound = core.bind_due_frontier(transaction)
            core.apply_transaction(bound, deterministic_policy=False)
            prepared_cores.append(core)
            prepared_snapshots.append(bound.post_membership_pre_policy_snapshot)
        return prepared_cores, prepared_snapshots

    def save_live_checkpoint(path: Path, payload: Mapping[str, Any]) -> None:
        temporary = path.with_suffix(path.suffix + ".tmp")
        torch.save(dict(payload), temporary)
        temporary.replace(path)

    pending_cores = None
    pending_snapshots = None
    if str(getattr(args, "resume_from", "") or ""):
        resume_path = Path(args.resume_from).resolve()
        if resume_path.parent != checkpoint_dir.resolve():
            raise ValueError("Stage C resume checkpoint must belong to this arm root")
        resume_payload = torch.load(resume_path, map_location=device, weights_only=False)
        runtime_payloads = list(
            resume_payload["event_architecture"]["runtime_payloads"]
        )
        restore_cores = []
        for env_index, runtime_payload in enumerate(runtime_payloads):
            rng = runtime_payload["rng_ledger"]
            restore_cores.append(
                _make_event_runtime(
                    model_owner,
                    environment_index=env_index,
                    episode_id=int(rng["episode_id"]),
                    event_master_seed=int(rng["opportunity"]["master_seed"]),
                    action_master_seed=int(rng["policy_action"]["master_seed"]),
                )
            )
        optimizer_states, restored_normalizers, counters = (
            restore_vector_event_checkpoint(
                resume_payload,
                model_owner=model_owner,
                cores=restore_cores,
                collector=collector,
            )
        )
        high_optimizer.load_state_dict(optimizer_states["high"])
        low_optimizer.load_state_dict(optimizer_states["low"])
        normalizer_states = restored_normalizers
        total_steps = int(counters["total_steps"])
        update_idx = int(counters["update_idx"])
        high_optimizer_steps = int(counters["high_optimizer_steps"])
        low_optimizer_steps = int(counters["low_optimizer_steps"])
        next_episode_id = int(counters["next_episode_id"])
        intrinsic_applied_count = int(counters["intrinsic_applied_count"])
        if not 0 <= update_idx < 250:
            raise ValueError("Stage C resume update lies outside the active run")
        expected_next_episode_id = num_envs if update_idx == 0 else update_idx * num_envs
        if (
            total_steps != update_idx * num_envs * HORIZON
            or high_optimizer_steps != update_idx * 4
            or low_optimizer_steps != update_idx * 4
            or next_episode_id != expected_next_episode_id
            or intrinsic_applied_count != 0
        ):
            raise ValueError("Stage C resume counter ledger mismatch")
        if not update_path.is_file():
            raise FileNotFoundError("Stage C resume requires train_updates.csv")
        with update_path.open("r", encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        if len(rows) < update_idx:
            raise ValueError("Stage C resume training ledger trails its checkpoint")
        if len(rows) > update_idx:
            rows = rows[:update_idx]
            _write_event_csv_rows(
                update_path, fieldnames=update_fields, rows=rows
            )
        for name in maximum_replay_errors:
            maximum_replay_errors[name] = max(
                (float(row[name]) for row in rows), default=0.0
            )
        finite_updates = all(bool(int(float(row["finite_update"]))) for row in rows)
        if update_idx == 0:
            pending_cores = restore_cores
            pending_snapshots = [
                runtime_payload["current_observation_state_boundary"]["snapshot"]
                for runtime_payload in runtime_payloads
            ]
        resumed_from = str(resume_path)
    else:
        if update_path.exists():
            raise FileExistsError("fresh Stage C arm root already has train_updates.csv")
        _write_event_csv_rows(update_path, fieldnames=update_fields, rows=[])
        initial_episode_ids = tuple(range(num_envs))
        pending_cores, pending_snapshots = prepare_episode_batch(initial_episode_ids)
        next_episode_id = num_envs
        initial_boundaries = [
            {
                "physical_time": int(core.physical_time),
                "episode_id": int(core.rng_episode_id),
                "terminal": False,
                "snapshot": snapshot,
            }
            for core, snapshot in zip(pending_cores, pending_snapshots)
        ]
        update_zero_checkpoint = vector_event_checkpoint_payload(
            model_owner=model_owner,
            cores=pending_cores,
            collector_snapshot=collector.snapshot_event_runtime(),
            current_boundaries=initial_boundaries,
            optimizer_states={
                "high": high_optimizer.state_dict(),
                "low": low_optimizer.state_dict(),
            },
            normalizer_states=normalizer_states,
            counters={
                "total_steps": 0,
                "update_idx": 0,
                "high_optimizer_steps": 0,
                "low_optimizer_steps": 0,
                "next_episode_id": next_episode_id,
                "intrinsic_applied_count": 0,
            },
        )
        for path in _event_live_checkpoint_paths(
            checkpoint_dir, update_idx=0, save_interval=int(args.save_interval)
        ):
            save_live_checkpoint(path, update_zero_checkpoint)

    start_time = time.perf_counter()
    final_cores = None
    final_boundaries = None
    try:
        with update_path.open("a", encoding="utf-8", newline="") as handle:
            csv_writer = csv.DictWriter(handle, fieldnames=update_fields)
            for update_idx in range(update_idx + 1, 251):
                if pending_cores is not None and pending_snapshots is not None:
                    cores = pending_cores
                    snapshots = pending_snapshots
                    pending_cores = None
                    pending_snapshots = None
                else:
                    episode_ids = tuple(
                        range(next_episode_id, next_episode_id + num_envs)
                    )
                    next_episode_id += num_envs
                    cores, snapshots = prepare_episode_batch(episode_ids)

                for primitive_time in range(HORIZON):
                    low_batch = batched_low_step(cores, snapshots)
                    steps = collector.step_event_runtime(low_batch.routed_actions)
                    next_snapshots = []
                    for core, step in zip(cores, steps):
                        if bool(step.truncated):
                            raise RuntimeError(
                                "generic-SHORT Stage C does not admit truncation"
                            )
                        intrinsic_applied_count += int(
                            step.info.get("intrinsic_reward_applied_count", -1)
                        )
                        if float(step.info.get("intrinsic_reward", float("nan"))) != 0.0:
                            raise RuntimeError(
                                "Stage C intrinsic reward must remain exactly zero"
                            )
                        core.complete_primitive_transition(float(step.reward))
                        if bool(step.terminated):
                            if primitive_time != HORIZON - 1 or step.next_transaction is not None:
                                raise RuntimeError(
                                    "generic-SHORT terminal boundary is inconsistent"
                                )
                            core.close_terminal()
                            next_snapshots.append(None)
                        else:
                            if step.next_transaction is None:
                                raise RuntimeError(
                                    "nonterminal event step is missing its next transaction"
                                )
                            bound = core.bind_due_frontier(step.next_transaction)
                            core.apply_transaction(bound, deterministic_policy=False)
                            next_snapshots.append(
                                bound.post_membership_pre_policy_snapshot
                            )
                    snapshots = next_snapshots
                    total_steps += num_envs
                if intrinsic_applied_count != 0:
                    raise RuntimeError("Stage C intrinsic-applied count must be zero")
                first_pass_replay = None
                packed_ppo = pack_event_ppo_data(cores)
                for ppo_pass in range(4):
                    metrics = apply_event_ppo_update(
                        packed_ppo,
                        high_optimizer=high_optimizer,
                        low_optimizer=low_optimizer,
                    )
                    if ppo_pass == 0:
                        first_pass_replay = {
                            name: float(metrics[name])
                            for name in maximum_replay_errors
                        }
                    high_optimizer_steps += 1
                    low_optimizer_steps += 1
                assert first_pass_replay is not None
                for name, value in first_pass_replay.items():
                    maximum_replay_errors[name] = max(
                        maximum_replay_errors[name], value
                    )
                last_metrics = {name: float(value) for name, value in metrics.items()}
                finite_update = bool(
                    all(np.isfinite(value) for value in last_metrics.values())
                    and _event_state_dict_finite(model_owner)
                )
                finite_updates = finite_updates and finite_update
                update_row = {
                    "update": update_idx,
                    "steps": total_steps,
                    "high_optimizer_steps": high_optimizer_steps,
                    "low_optimizer_steps": low_optimizer_steps,
                    **maximum_replay_errors,
                    "high_loss": last_metrics["high_loss"],
                    "low_loss": last_metrics["low_loss"],
                    "finite_update": int(finite_update),
                }
                csv_writer.writerow(update_row)
                handle.flush()
                final_cores = cores
                final_boundaries = [
                    {
                        "physical_time": int(core.physical_time),
                        "episode_id": int(core.rng_episode_id),
                        "terminal": True,
                    }
                    for core in cores
                ]
                checkpoint = vector_event_checkpoint_payload(
                    model_owner=model_owner,
                    cores=cores,
                    collector_snapshot=collector.snapshot_event_runtime(),
                    current_boundaries=final_boundaries,
                    optimizer_states={
                        "high": high_optimizer.state_dict(),
                        "low": low_optimizer.state_dict(),
                    },
                    normalizer_states=normalizer_states,
                    counters={
                        "total_steps": total_steps,
                        "update_idx": update_idx,
                        "high_optimizer_steps": high_optimizer_steps,
                        "low_optimizer_steps": low_optimizer_steps,
                        "next_episode_id": next_episode_id,
                        "intrinsic_applied_count": intrinsic_applied_count,
                    },
                )
                for path in _event_live_checkpoint_paths(
                    checkpoint_dir,
                    update_idx=update_idx,
                    save_interval=int(args.save_interval),
                ):
                    save_live_checkpoint(path, checkpoint)
                _write_event_arm_status(
                    args,
                    state="running",
                    phase="training",
                    mode=config.event_architecture_mode,
                    update=update_idx,
                    updates_total=250,
                    steps=total_steps,
                    steps_total=320_000,
                    high_optimizer_steps=high_optimizer_steps,
                    low_optimizer_steps=low_optimizer_steps,
                    optimizer_steps_total=1_000,
                    checkpoint_path=str(latest_checkpoint_path),
                )
                if writer is not None:
                    for name, value in last_metrics.items():
                        writer.add_scalar(f"Event/{name}", value, total_steps)
                    writer.flush()
                emit(
                    args,
                    "event_update "
                    f"mode={config.event_architecture_mode} update={update_idx}/250 "
                    f"steps={total_steps} high_optimizer_steps={high_optimizer_steps} "
                    f"low_optimizer_steps={low_optimizer_steps}",
                )

        if final_cores is None or final_boundaries is None:
            raise RuntimeError("Stage C produced no final vector boundary")
        if (
            total_steps != 320_000
            or high_optimizer_steps != 1_000
            or low_optimizer_steps != 1_000
            or next_episode_id != 4_000
            or intrinsic_applied_count != 0
        ):
            raise RuntimeError("Stage C exposure ledger is not exact")

        final_eval_checkpoint = checkpoint_dir / "update_250_eval.pt"
        torch.save(
            event_model_only_checkpoint_payload(
                model_owner=model_owner,
                normalizer_states=normalizer_states,
                total_steps=total_steps,
                update_idx=update_idx,
            ),
            final_eval_checkpoint,
        )
        final_owner = _make_event_model_owner(config, device)
        restore_event_model_only_checkpoint(
            torch.load(final_eval_checkpoint, map_location=device, weights_only=False),
            model_owner=final_owner,
        )
        _write_event_arm_status(
            args,
            state="running",
            phase="final_evaluation",
            mode=config.event_architecture_mode,
            update=250,
            updates_total=250,
            steps=320_000,
            steps_total=320_000,
            high_optimizer_steps=1_000,
            low_optimizer_steps=1_000,
            optimizer_steps_total=1_000,
        )
        final_deterministic = _evaluate_event_model(
            final_owner,
            deterministic=True,
            capture_prefix=False,
            capture_forced_audit=False,
        )
        _write_event_arm_status(
            args,
            state="running",
            phase="forced_audit_and_stochastic_evaluation",
            mode=config.event_architecture_mode,
            update=250,
            updates_total=250,
            steps=320_000,
            steps_total=320_000,
            high_optimizer_steps=1_000,
            low_optimizer_steps=1_000,
            optimizer_steps_total=1_000,
        )
        final_stochastic = _evaluate_event_model(
            final_owner,
            deterministic=False,
            capture_prefix=True,
            capture_forced_audit=True,
        )

        live_payload = torch.load(
            latest_checkpoint_path, map_location=device, weights_only=False
        )
        verification_owner = _make_event_model_owner(config, device)
        verification_envs = [
            DynamicRosterEventEnv(task_master_seed=TRAIN_LEDGER_SEED)
            for _ in range(num_envs)
        ]
        verification_collector = SyncEnvCollector(verification_envs)
        runtime_payloads = live_payload["event_architecture"]["runtime_payloads"]
        verification_cores = []
        for env_index, runtime_payload in enumerate(runtime_payloads):
            rng = runtime_payload["rng_ledger"]
            verification_cores.append(
                _make_event_runtime(
                    verification_owner,
                    environment_index=env_index,
                    episode_id=int(rng["episode_id"]),
                    event_master_seed=int(rng["opportunity"]["master_seed"]),
                    action_master_seed=int(rng["policy_action"]["master_seed"]),
                )
            )
        restored_optimizers, restored_normalizers, restored_counters = (
            restore_vector_event_checkpoint(
                live_payload,
                model_owner=verification_owner,
                cores=verification_cores,
                collector=verification_collector,
            )
        )
        restored_collector_snapshot = verification_collector.snapshot_event_runtime()
        roundtrip_payload = vector_event_checkpoint_payload(
            model_owner=verification_owner,
            cores=verification_cores,
            collector_snapshot=restored_collector_snapshot,
            current_boundaries=[
                runtime_payload["current_observation_state_boundary"]
                for runtime_payload in runtime_payloads
            ],
            optimizer_states=restored_optimizers,
            normalizer_states=restored_normalizers,
            counters=restored_counters,
        )
        checkpoint_state_error = _nested_state_maximum_difference(
            model_state(model_owner), model_state(verification_owner)
        )
        checkpoint_runtime_error = _nested_state_maximum_difference(
            runtime_payloads,
            roundtrip_payload["event_architecture"]["runtime_payloads"],
        )
        checkpoint_collector_error = _nested_state_maximum_difference(
            live_payload["event_architecture"]["collector_snapshot"],
            restored_collector_snapshot,
        )
        checkpoint_optimizer_error = max(
            _nested_state_maximum_difference(
                high_optimizer.state_dict(), restored_optimizers["high"]
            ),
            _nested_state_maximum_difference(
                low_optimizer.state_dict(), restored_optimizers["low"]
            ),
        )
        checkpoint_normalizer_error = _nested_state_maximum_difference(
            normalizer_states, restored_normalizers
        )
        checkpoint_counter_error = _nested_state_maximum_difference(
            {
                "total_steps": total_steps,
                "update_idx": update_idx,
                "high_optimizer_steps": high_optimizer_steps,
                "low_optimizer_steps": low_optimizer_steps,
                "next_episode_id": next_episode_id,
                "intrinsic_applied_count": intrinsic_applied_count,
            },
            restored_counters,
        )
        verification_collector.close()

        final_state = model_state(model_owner)
        parameter_drift = _nested_state_maximum_difference(initial_state, final_state)
        forced_audit = final_stochastic["forced_audit"]
        prefix_rows = final_stochastic["prefix_rows"]
        persistent_skill = int(forced_audit["persistent_like_skill"])
        prefix_summary = _summarize_event_prefix_rows(
            prefix_rows,
            persistent_skill=persistent_skill,
            architecture_mode=model_owner.architecture_mode,
        )
        prefix_actual_replay_logp_max = float(
            prefix_summary["actual_replay_logp_max_error"]
        )
        prefix_actual_replay_probability_max = float(
            prefix_summary["actual_replay_probability_max_error"]
        )
        zero_det = zero_evaluation["deterministic"]
        final_det = final_deterministic
        improvement_ci = _paired_mean_ci(
            np.asarray(final_det["utility"], dtype=np.float64)
            - np.asarray(zero_det["utility"], dtype=np.float64),
            seed=107_057,
        )
        m0 = {
            "formal_contract_exact": True,
            "environment_steps_exact": total_steps == 320_000,
            "high_optimizer_steps_exact": high_optimizer_steps == 1_000,
            "low_optimizer_steps_exact": low_optimizer_steps == 1_000,
            "training_ledger_ids_exact": next_episode_id == 4_000,
            "zero_evaluation_exact": all(
                len(zero_evaluation[name]["utility"]) == 256
                for name in ("deterministic", "stochastic")
            ),
            "final_evaluation_exact": len(final_deterministic["utility"]) == 256
            and len(final_stochastic["utility"]) == 256,
            "forced_audit_exact": forced_audit["effect_shape"] == [128, 3, 2, 4]
            and forced_audit["forced_environment_steps"] == 9_216,
            "intrinsic_reward_and_count_zero": intrinsic_applied_count == 0,
            "sampling_replay_probability": max(
                maximum_replay_errors["high_logp_max_error"],
                maximum_replay_errors["low_logp_max_error"],
            )
            <= 1e-6,
            "sampling_replay_value": max(
                maximum_replay_errors["high_value_max_error"],
                maximum_replay_errors["low_value_max_error"],
            )
            <= 1e-6,
            "natural_probability_read_replay": max(
                prefix_actual_replay_logp_max,
                prefix_actual_replay_probability_max,
            )
            <= 1e-6,
            "all_updates_finite": bool(finite_updates),
            "final_parameters_finite": _event_state_dict_finite(model_owner),
            "parameter_update_nonzero": parameter_drift > 1e-8,
            "strict_vector_schema3_resume": checkpoint_state_error == 0.0
            and checkpoint_runtime_error == 0.0
            and checkpoint_collector_error == 0.0
            and checkpoint_optimizer_error == 0.0
            and checkpoint_normalizer_error == 0.0
            and checkpoint_counter_error == 0.0,
            "f0_common_support_reduction": model_owner.architecture_mode != "f0"
            or float(prefix_summary["f0_common_support_tv_max"] or 0.0) <= 1e-6,
        }
        implementation_valid = all(bool(value) for value in m0.values())
        final_deterministic_result = {
            key: value
            for key, value in final_deterministic.items()
            if key not in {"prefix_rows", "timing_rows", "forced_audit"}
        }
        final_stochastic_result = {
            key: value
            for key, value in final_stochastic.items()
            if key not in {"prefix_rows", "timing_rows", "forced_audit"}
        }
        arm_result = {
            "schema_version": 1,
            "stage": "stage_c_paired_f0_f1",
            "arm": model_owner.architecture_mode,
            "implementation_valid": implementation_valid,
            "m0": m0,
            "contract": {
                "num_envs": 16,
                "horizon": 80,
                "rollout_length": 80,
                "outer_updates": 250,
                "environment_transitions": 320_000,
                "ppo_passes_per_update": 4,
                "high_optimizer_steps": 1_000,
                "low_optimizer_steps": 1_000,
                "latent_skills": 3,
                "optimizer": "Adam",
                "learning_rate": 3e-4,
                "gamma": 0.99,
                "gae_lambda": 0.95,
                "policy_clip": 0.20,
                "value_clip": 0.20,
                "value_coefficient": 0.50,
                "entropy_coefficient": 0.01,
                "gradient_clip": 0.50,
                "evaluation_episodes_per_mode": 256,
                "bootstrap_repetitions": 10_000,
                "bootstrap_seed": 107_057,
                "selector": (
                    "initial_summary"
                    if model_owner.architecture_mode == "f0"
                    else "working_summary"
                ),
            },
            "counts": {
                "environment_steps": total_steps,
                "high_optimizer_steps": high_optimizer_steps,
                "low_optimizer_steps": low_optimizer_steps,
                "training_ledger_ids": next_episode_id,
                "intrinsic_applied_count": intrinsic_applied_count,
            },
            "resume": {
                "resumed_from": resumed_from,
                "strict_resume_verified": bool(m0["strict_vector_schema3_resume"]),
            },
            "replay": maximum_replay_errors,
            "parameter_drift_max_abs": parameter_drift,
            "checkpoint_state_max_error": checkpoint_state_error,
            "checkpoint_runtime_max_error": checkpoint_runtime_error,
            "checkpoint_collector_max_error": checkpoint_collector_error,
            "checkpoint_optimizer_max_error": checkpoint_optimizer_error,
            "checkpoint_normalizer_max_error": checkpoint_normalizer_error,
            "checkpoint_counter_max_error": checkpoint_counter_error,
            "zero": zero_evaluation,
            "final": {
                "deterministic": final_deterministic_result,
                "stochastic": final_stochastic_result,
            },
            "paired_final_minus_zero_deterministic_utility_ci95": improvement_ci,
            "prefix": prefix_summary,
            "forced_audit": forced_audit,
            "timing_rows": final_stochastic["timing_rows"],
            "last_update_metrics": last_metrics,
            "wall_seconds": time.perf_counter() - start_time,
        }
        arm_result_path = result_dir / "stage_c_arm.json"
        _write_event_json(arm_result_path, arm_result)
        _write_event_arm_status(
            args,
            state="complete",
            phase="terminal",
            mode=config.event_architecture_mode,
            update=250,
            updates_total=250,
            steps=320_000,
            steps_total=320_000,
            high_optimizer_steps=1_000,
            low_optimizer_steps=1_000,
            optimizer_steps_total=1_000,
            implementation_valid=implementation_valid,
            result_path=str(arm_result_path),
            checkpoint_path=str(latest_checkpoint_path),
        )
        return model_owner, total_steps, update_idx
    finally:
        collector.close()
