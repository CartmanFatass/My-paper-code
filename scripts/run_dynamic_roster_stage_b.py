"""Run the frozen Stage-B direct primitive-AR access instrument."""

from __future__ import annotations

import argparse
import csv
from datetime import datetime
import json
from pathlib import Path
import sys
import time
import traceback
from typing import Any, Callable

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np
import torch

from ha_ctse_process.dynamic_roster_direct import (
    BOOTSTRAP_SEED,
    EVAL_LEDGER_SEED,
    GRADIENT_CLIP,
    HIDDEN_DIM,
    LEARNING_RATE,
    MAX_RECURRENT_CHUNK,
    MODEL_INITIALIZATION_SEED,
    POLICY_ACTION_SEED,
    PPO_PASSES,
    REPLAY_TOLERANCE,
    TRAIN_LEDGER_SEED,
    DirectPrimitiveARPolicy,
    collect_direct_trajectory,
    evaluate_direct_policy,
    hidden_lifecycle_contract_valid,
    json_ready,
    load_checkpoint,
    make_action_uniforms,
    maximum_state_difference,
    model_state_copy,
    nested_state_maximum_difference,
    optimize_direct_update,
    paired_bootstrap_ci,
    save_checkpoint,
    state_dict_finite,
)
from ha_ctse_process.dynamic_roster_testbed import (
    HORIZON,
    DynamicRosterLedger,
    GenericShortDynamicRosterEnv,
)


FORMAL_NUM_ENVS = 16
FORMAL_UPDATES = 250
FORMAL_EVAL_EPISODES = 256
EXPECTED_ACTIVE_ROWS_PER_EPISODE = 320


def _write_status(path: Path, **fields: Any) -> None:
    fields = {
        **fields,
        "updated": datetime.now().astimezone().isoformat(timespec="seconds"),
    }
    path.write_text(
        "".join(f"{key}={value}\n" for key, value in fields.items()),
        encoding="utf-8",
    )


def _evaluation_payload(values: dict[str, Any]) -> dict[str, Any]:
    return {
        "episode_ids": values["episode_ids"],
        "persistent": values["persistent"],
        "short": values["short"],
        "utility": values["utility"],
        "persistent_mean": values["persistent_mean"],
        "short_mean": values["short_mean"],
        "utility_mean": values["utility_mean"],
    }


def run_stage_b(
    *,
    output_root: Path,
    device_name: str,
    num_envs: int,
    updates: int,
    eval_episodes: int,
    smoke: bool,
    resume_checkpoint: Path | None = None,
    ledger_factory: Callable[..., DynamicRosterLedger] | None = None,
    environment_factory: Callable[
        [DynamicRosterLedger], GenericShortDynamicRosterEnv
    ] | None = None,
) -> dict[str, Any]:
    formal = not smoke
    if formal and (
        num_envs != FORMAL_NUM_ENVS
        or updates != FORMAL_UPDATES
        or eval_episodes != FORMAL_EVAL_EPISODES
        or device_name != "cuda"
    ):
        raise ValueError("formal Stage B must use the exact frozen CUDA contract")
    if num_envs <= 0 or updates <= 0 or eval_episodes <= 0:
        raise ValueError("Stage B counts must be positive")
    if device_name == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("Stage B requested CUDA but CUDA is unavailable")

    output_root.mkdir(parents=True, exist_ok=True)
    checkpoint_dir = output_root / "checkpoints"
    result_dir = output_root / "result"
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    result_dir.mkdir(parents=True, exist_ok=True)
    status_path = output_root / "runner_status.txt"
    update_path = output_root / "train_updates.csv"
    device = torch.device(device_name)

    torch.manual_seed(MODEL_INITIALIZATION_SEED)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(MODEL_INITIALIZATION_SEED)
    model = DirectPrimitiveARPolicy().to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=LEARNING_RATE)
    evaluation_ids = tuple(range(eval_episodes))
    evaluation_uniforms = make_action_uniforms(evaluation_ids)

    zero_path = checkpoint_dir / "update_000.pt"
    if resume_checkpoint is None:
        save_checkpoint(
            zero_path,
            model=model,
            optimizer=optimizer,
            completed_updates=0,
            next_ledger_id=0,
        )
    elif not zero_path.is_file():
        raise FileNotFoundError("resume requires the original update_000 checkpoint")

    zero_model = DirectPrimitiveARPolicy().to(device)
    zero_optimizer = torch.optim.Adam(zero_model.parameters(), lr=LEARNING_RATE)
    load_checkpoint(zero_path, model=zero_model, optimizer=zero_optimizer)
    initial_state = model_state_copy(zero_model)

    start_update = 0
    if resume_checkpoint is not None:
        resume_path = resume_checkpoint.resolve()
        if resume_path.parent != checkpoint_dir.resolve():
            raise ValueError("resume checkpoint must belong to this run root")
        resume_bundle = load_checkpoint(
            resume_path, model=model, optimizer=optimizer
        )
        start_update = int(resume_bundle["completed_updates"])
        if not 0 < start_update < updates:
            raise ValueError("resume checkpoint update lies outside the active run")
        if int(resume_bundle["next_ledger_id"]) != start_update * num_envs:
            raise ValueError("resume checkpoint ledger counter mismatch")
    _write_status(
        status_path,
        state="running",
        phase="zero_evaluation",
        update=start_update,
        updates_total=updates,
        environment_steps=start_update * num_envs * HORIZON,
        optimizer_steps=start_update * PPO_PASSES,
    )
    zero_deterministic = evaluate_direct_policy(
        zero_model,
        episode_ids=evaluation_ids,
        deterministic=True,
        device=device,
        ledger_factory=ledger_factory,
        environment_factory=environment_factory,
    )
    zero_stochastic = evaluate_direct_policy(
        zero_model,
        episode_ids=evaluation_ids,
        deterministic=False,
        device=device,
        uniforms=evaluation_uniforms,
        ledger_factory=ledger_factory,
        environment_factory=environment_factory,
    )

    fieldnames = [
        "update",
        "ledger_start",
        "ledger_end",
        "environment_steps",
        "active_agent_rows",
        "optimizer_steps",
        "utility_mean",
        "persistent_mean",
        "short_mean",
        "policy_loss",
        "value_loss",
        "entropy",
        "clip_fraction",
        "gradient_norm",
        "logp_max_error",
        "joint_logp_max_error",
        "value_max_error",
        "hidden_max_error",
        "prefix_max_error",
        "finite_update",
        "hidden_lifecycle_valid",
    ]
    maximum_errors = {
        "logp_max_error": 0.0,
        "joint_logp_max_error": 0.0,
        "value_max_error": 0.0,
        "hidden_max_error": 0.0,
        "prefix_max_error": 0.0,
    }
    optimizer_steps = start_update * PPO_PASSES
    environment_steps = start_update * num_envs * HORIZON
    active_agent_rows = (
        start_update * num_envs * EXPECTED_ACTIVE_ROWS_PER_EPISODE
    )
    finite_updates = True
    hidden_lifecycle_valid = True
    consumed_ledger_ids: list[int] = []
    start_time = time.perf_counter()
    last_metrics: dict[str, float] = {}
    if start_update:
        if not update_path.is_file():
            raise FileNotFoundError("resume requires the existing training ledger")
        with update_path.open("r", encoding="utf-8", newline="") as existing:
            reader = csv.DictReader(existing)
            if reader.fieldnames != fieldnames:
                raise ValueError("resume training ledger schema mismatch")
            previous_rows = list(reader)
        if len(previous_rows) != start_update:
            raise ValueError("resume training ledger row count mismatch")
        for row_index, row in enumerate(previous_rows):
            expected_start = row_index * num_envs
            expected_end = expected_start + num_envs - 1
            if (
                int(row["update"]) != row_index + 1
                or int(row["ledger_start"]) != expected_start
                or int(row["ledger_end"]) != expected_end
            ):
                raise ValueError("resume training ledger ID sequence mismatch")
            consumed_ledger_ids.extend(range(expected_start, expected_end + 1))
            finite_updates = finite_updates and bool(float(row["finite_update"]))
            hidden_lifecycle_valid = hidden_lifecycle_valid and bool(
                float(row["hidden_lifecycle_valid"])
            )
            for name in maximum_errors:
                maximum_errors[name] = max(
                    maximum_errors[name], float(row[name])
                )
        final_previous = previous_rows[-1]
        if (
            int(float(final_previous["environment_steps"])) != environment_steps
            or int(float(final_previous["active_agent_rows"])) != active_agent_rows
            or int(float(final_previous["optimizer_steps"])) != optimizer_steps
        ):
            raise ValueError("resume cumulative counter mismatch")
        open_mode = "a"
    else:
        if update_path.exists():
            raise FileExistsError("fresh run root already contains a training ledger")
        open_mode = "w"

    with update_path.open(open_mode, encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        if start_update == 0:
            writer.writeheader()
        for update_index in range(start_update, updates):
            first_ledger = update_index * num_envs
            ledger_ids = range(first_ledger, first_ledger + num_envs)
            trajectory = collect_direct_trajectory(
                model,
                ledger_ids=ledger_ids,
                ledger_seed=TRAIN_LEDGER_SEED,
                device=device,
                ledger_factory=ledger_factory,
                environment_factory=environment_factory,
            )
            consumed_ledger_ids.extend(trajectory.ledger_ids)
            hidden_lifecycle_valid = (
                hidden_lifecycle_valid
                and hidden_lifecycle_contract_valid(trajectory)
            )
            metrics = optimize_direct_update(
                model,
                optimizer,
                trajectory,
                device=device,
                ppo_passes=PPO_PASSES,
            )
            environment_steps += trajectory.environment_steps
            active_agent_rows += trajectory.active_token_count
            optimizer_steps += PPO_PASSES
            finite_updates = finite_updates and bool(metrics["finite_update"])
            for name in maximum_errors:
                maximum_errors[name] = max(
                    maximum_errors[name], float(metrics[name])
                )
            utility_mean = float(
                np.mean([outcome.utility for outcome in trajectory.outcomes])
            )
            persistent_mean = float(
                np.mean(
                    [outcome.persistent_score for outcome in trajectory.outcomes]
                )
            )
            short_mean = float(
                np.mean([outcome.short_score for outcome in trajectory.outcomes])
            )
            last_metrics = metrics
            writer.writerow(
                {
                    "update": update_index + 1,
                    "ledger_start": trajectory.ledger_ids[0],
                    "ledger_end": trajectory.ledger_ids[-1],
                    "environment_steps": environment_steps,
                    "active_agent_rows": active_agent_rows,
                    "optimizer_steps": optimizer_steps,
                    "utility_mean": utility_mean,
                    "persistent_mean": persistent_mean,
                    "short_mean": short_mean,
                    "hidden_lifecycle_valid": float(
                        hidden_lifecycle_contract_valid(trajectory)
                    ),
                    **{
                        name: metrics[name]
                        for name in (
                            "policy_loss",
                            "value_loss",
                            "entropy",
                            "clip_fraction",
                            "gradient_norm",
                            "logp_max_error",
                            "joint_logp_max_error",
                            "value_max_error",
                            "hidden_max_error",
                            "prefix_max_error",
                            "finite_update",
                        )
                    },
                }
            )
            handle.flush()
            latest_path = checkpoint_dir / "latest.pt"
            save_checkpoint(
                latest_path,
                model=model,
                optimizer=optimizer,
                completed_updates=update_index + 1,
                next_ledger_id=(update_index + 1) * num_envs,
            )
            _write_status(
                status_path,
                state="running",
                phase="training",
                update=update_index + 1,
                updates_total=updates,
                environment_steps=environment_steps,
                environment_steps_total=updates * num_envs * HORIZON,
                optimizer_steps=optimizer_steps,
                optimizer_steps_total=updates * PPO_PASSES,
                utility_mean=f"{utility_mean:.8f}",
                replay_logp_max_error=f"{maximum_errors['logp_max_error']:.9g}",
            )

    final_path = checkpoint_dir / f"update_{updates:03d}.pt"
    save_checkpoint(
        final_path,
        model=model,
        optimizer=optimizer,
        completed_updates=updates,
        next_ledger_id=updates * num_envs,
    )
    final_state = model_state_copy(model)
    parameter_drift = maximum_state_difference(initial_state, final_state)

    reloaded = DirectPrimitiveARPolicy().to(device)
    reload_optimizer = torch.optim.Adam(reloaded.parameters(), lr=LEARNING_RATE)
    checkpoint_bundle = load_checkpoint(
        final_path, model=reloaded, optimizer=reload_optimizer
    )
    checkpoint_state_error = maximum_state_difference(
        final_state, model_state_copy(reloaded)
    )
    checkpoint_optimizer_error = nested_state_maximum_difference(
        checkpoint_bundle["optimizer_state"], reload_optimizer.state_dict()
    )
    _write_status(
        status_path,
        state="running",
        phase="final_evaluation",
        update=updates,
        updates_total=updates,
        environment_steps=environment_steps,
        optimizer_steps=optimizer_steps,
    )
    final_deterministic = evaluate_direct_policy(
        reloaded,
        episode_ids=evaluation_ids,
        deterministic=True,
        device=device,
        ledger_factory=ledger_factory,
        environment_factory=environment_factory,
    )
    final_stochastic = evaluate_direct_policy(
        reloaded,
        episode_ids=evaluation_ids,
        deterministic=False,
        device=device,
        uniforms=evaluation_uniforms,
        ledger_factory=ledger_factory,
        environment_factory=environment_factory,
    )
    improvement_ci = paired_bootstrap_ci(
        final_deterministic["utility"] - zero_deterministic["utility"],
        repetitions=10_000,
        seed=BOOTSTRAP_SEED,
    )

    expected_environment_steps = updates * num_envs * HORIZON
    expected_active_rows = (
        updates * num_envs * EXPECTED_ACTIVE_ROWS_PER_EPISODE
    )
    expected_optimizer_steps = updates * PPO_PASSES
    formal_contract_exact = bool(
        formal
        and num_envs == FORMAL_NUM_ENVS
        and updates == FORMAL_UPDATES
        and eval_episodes == FORMAL_EVAL_EPISODES
        and device_name == "cuda"
    )
    requested_contract_valid = formal_contract_exact if formal else bool(
        smoke and num_envs > 0 and updates > 0 and eval_episodes > 0
    )
    m0 = {
        "requested_contract_valid": requested_contract_valid,
        "environment_steps_exact": environment_steps
        == expected_environment_steps,
        "active_agent_rows_exact": active_agent_rows == expected_active_rows,
        "optimizer_steps_exact": optimizer_steps == expected_optimizer_steps,
        "train_ledger_ids_exact": tuple(consumed_ledger_ids)
        == tuple(range(updates * num_envs)),
        "evaluation_ledger_ids_exact": evaluation_ids == tuple(range(eval_episodes)),
        "sampling_replay_logp": maximum_errors["logp_max_error"]
        <= REPLAY_TOLERANCE,
        "sampling_replay_joint_logp": maximum_errors["joint_logp_max_error"]
        <= REPLAY_TOLERANCE,
        "sampling_replay_value": maximum_errors["value_max_error"]
        <= REPLAY_TOLERANCE,
        "recurrent_hidden_replay": maximum_errors["hidden_max_error"]
        <= REPLAY_TOLERANCE,
        "prefix_replay": maximum_errors["prefix_max_error"]
        <= REPLAY_TOLERANCE,
        "all_updates_finite": bool(finite_updates),
        "final_parameters_finite": state_dict_finite(final_state),
        "parameter_update_nonzero": parameter_drift > 1e-8,
        "strict_schema3_checkpoint": int(checkpoint_bundle["schema_version"]) == 3,
        "exact_final_checkpoint": checkpoint_state_error == 0.0
        and checkpoint_optimizer_error == 0.0
        and int(checkpoint_bundle["completed_updates"]) == updates
        and int(checkpoint_bundle["next_ledger_id"]) == updates * num_envs,
        "temporary_absence_hidden_frozen": hidden_lifecycle_valid,
    }
    static_reviewed_invariants = {
        "single_joint_optimizer": True,
        "team_value_and_token_factor_ratio": True,
        "active_only_anonymous_actor": True,
        "skill_high_intrinsic_code_paths_absent": True,
    }
    implementation_valid = all(bool(value) for value in m0.values()) and all(
        bool(value) for value in static_reviewed_invariants.values()
    )
    direct_access = bool(
        final_deterministic["utility_mean"] >= 0.70
        and final_deterministic["persistent_mean"] >= 0.65
        and final_deterministic["short_mean"] >= 0.65
        and final_stochastic["utility_mean"] >= 0.60
        and improvement_ci[0] > 0.15
    )
    if smoke:
        status = "SMOKE_COMPLETE" if implementation_valid else "SMOKE_INVALID"
        next_action = "run the unchanged formal Stage B contract" if implementation_valid else "repair only the concrete smoke defect"
    elif not implementation_valid:
        status = "INVALID_IMPLEMENTATION"
        next_action = "repair only the concrete Stage B implementation defect"
    elif direct_access:
        status = "PASS_STAGE_B_DIRECT_ACCESS"
        next_action = "request the separately registered paired F0/F1 implementation boundary"
    else:
        status = "RETIRE_TESTBED_NO_DIRECT_ACCESS"
        next_action = "retire this exact testbed and do not run F0/F1"

    result = {
        "schema_version": 1,
        "stage": "stage_b_direct_primitive_ar_access",
        "status": status,
        "implementation_valid": implementation_valid,
        "direct_access_pass": direct_access if formal else None,
        "m0": m0,
        "static_reviewed_invariants": static_reviewed_invariants,
        "contract": {
            "num_envs": num_envs,
            "horizon": HORIZON,
            "rollout_length": HORIZON,
            "outer_updates": updates,
            "environment_transitions": expected_environment_steps,
            "ppo_passes_per_update": PPO_PASSES,
            "optimizer_steps": expected_optimizer_steps,
            "optimizer": "Adam",
            "learning_rate": LEARNING_RATE,
            "hidden_dim": HIDDEN_DIM,
            "model_parameters": model.parameter_count,
            "max_recurrent_chunk": MAX_RECURRENT_CHUNK,
            "gradient_clip": GRADIENT_CLIP,
            "ppo_estimand": "token_factor_clipping_with_shared_team_advantage",
            "critic_estimand": "one_team_value_per_environment_step",
            "prefix_encoding": "raw_earlier_action_counts",
            "model_initialization_seed": MODEL_INITIALIZATION_SEED,
            "training_task_ledger_seed": TRAIN_LEDGER_SEED,
            "policy_action_seed": POLICY_ACTION_SEED,
            "evaluation_ledger_seed": EVAL_LEDGER_SEED,
            "bootstrap_seed": BOOTSTRAP_SEED,
            "evaluation_episodes_per_mode": eval_episodes,
        },
        "counts": {
            "environment_steps": environment_steps,
            "active_agent_rows": active_agent_rows,
            "optimizer_steps": optimizer_steps,
            "skill_updates": 0,
            "high_updates": 0,
            "intrinsic_reward_reads": 0,
            "training_ledger_ids_consumed": len(consumed_ledger_ids),
        },
        "resume": {
            "resumed_from_checkpoint": (
                str(resume_checkpoint.resolve())
                if resume_checkpoint is not None
                else None
            ),
            "start_update": start_update,
        },
        "replay": maximum_errors,
        "parameter_drift_max_abs": parameter_drift,
        "checkpoint_state_max_error": checkpoint_state_error,
        "checkpoint_optimizer_max_error": checkpoint_optimizer_error,
        "zero": {
            "deterministic": _evaluation_payload(zero_deterministic),
            "stochastic": _evaluation_payload(zero_stochastic),
        },
        "final": {
            "deterministic": _evaluation_payload(final_deterministic),
            "stochastic": _evaluation_payload(final_stochastic),
        },
        "paired_final_minus_zero_deterministic_utility_ci95": improvement_ci,
        "thresholds": {
            "final_deterministic_utility_min": 0.70,
            "final_deterministic_persistent_min": 0.65,
            "final_deterministic_short_min": 0.65,
            "final_stochastic_utility_min": 0.60,
            "paired_improvement_lcb_exclusive": 0.15,
            "replay_tolerance": REPLAY_TOLERANCE,
        },
        "last_update_metrics": last_metrics,
        "wall_seconds": time.perf_counter() - start_time,
        "authoritative_status_source": str(status_path),
        "next_action": next_action,
    }
    result_path = result_dir / "stage_b_direct.json"
    result_path.write_text(
        json.dumps(json_ready(result), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    _write_status(
        status_path,
        state="complete",
        phase="terminal",
        status=status,
        update=updates,
        updates_total=updates,
        environment_steps=environment_steps,
        optimizer_steps=optimizer_steps,
        result=result_path,
    )
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--device", choices=("cpu", "cuda"), default="cuda")
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--num-envs", type=int, default=FORMAL_NUM_ENVS)
    parser.add_argument("--updates", type=int, default=FORMAL_UPDATES)
    parser.add_argument("--eval-episodes", type=int, default=FORMAL_EVAL_EPISODES)
    parser.add_argument("--resume-checkpoint", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    status_path = args.output_root / "runner_status.txt"
    try:
        result = run_stage_b(
            output_root=args.output_root,
            device_name=args.device,
            num_envs=args.num_envs,
            updates=args.updates,
            eval_episodes=args.eval_episodes,
            smoke=args.smoke,
            resume_checkpoint=args.resume_checkpoint,
        )
        print(json.dumps({
            "status": result["status"],
            "implementation_valid": result["implementation_valid"],
            "result": str(args.output_root / "result" / "stage_b_direct.json"),
        }, ensure_ascii=False))
        return 0
    except KeyboardInterrupt:
        args.output_root.mkdir(parents=True, exist_ok=True)
        _write_status(
            status_path,
            state="failed",
            phase="interrupted",
            error="KeyboardInterrupt",
        )
        raise
    except Exception as exc:
        args.output_root.mkdir(parents=True, exist_ok=True)
        (args.output_root / "runner_stderr.log").write_text(
            traceback.format_exc(), encoding="utf-8"
        )
        _write_status(
            status_path,
            state="failed",
            phase="runner",
            error=f"{type(exc).__name__}: {exc}",
        )
        raise


if __name__ == "__main__":
    sys.exit(main())
