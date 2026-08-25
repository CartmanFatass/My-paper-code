"""One-shot, same-treatment VNFC-B2 recovery under the cumulative eight-hour cap."""

from __future__ import annotations

import json
import math
import os
from datetime import datetime, timedelta
from pathlib import Path
import statistics
import subprocess
import sys
import tempfile
import time
from typing import Any, Mapping

import torch

from .analyze import analyze
from .config import BASE_SEEDS, EVENT_CELLS, LEARNED_ARMS, PRODUCTION_CONFIG
from .experiment import evaluate_models, peak_process_rss_bytes, save_checkpoint, train_arm
from .models import RecurrentSetActorCritic


ASSIGNMENT_ID = "VNFC-B2-TYPED-CAPSULE-RETENTION-v1"
CLOSURE_REVISION = "VNFC-B2-MATH-CLOSURE-20260812-01"
CHECKPOINT_SCHEMA = "VNFC-B2-PPO-CHECKPOINT-v1"
EXPECTED_OPTIMIZER_STEPS = (
    PRODUCTION_CONFIG.updates
    * PRODUCTION_CONFIG.ppo_epochs
    * math.ceil(
        PRODUCTION_CONFIG.episodes_per_update
        * PRODUCTION_CONFIG.episode_ticks
        * (sum(PRODUCTION_CONFIG.training_sizes) / len(PRODUCTION_CONFIG.training_sizes))
        / PRODUCTION_CONFIG.minibatch_agent_rows
    )
)
TERMINAL_REQUIRED_KEYS = {"command", "started_at", "ended_at", "exit_code"}


class RecoveryRefused(RuntimeError):
    pass


def _atomic_json(path: Path, payload: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
            json.dump(payload, stream, indent=2, sort_keys=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def _create_once(path: Path, payload: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8")
    try:
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError as exc:
        raise RecoveryRefused(f"exact-once recovery marker already exists: {path}") from exc
    with os.fdopen(fd, "wb") as stream:
        stream.write(encoded)
        stream.flush()
        os.fsync(stream.fileno())


def expected_manifest() -> dict[str, object]:
    probes = [RecurrentSetActorCritic() for _ in LEARNED_ARMS]
    parameter_counts = dict(zip(LEARNED_ARMS, (model.parameter_count for model in probes)))
    return {
        "artifact_kind": "VNFC_B2_PRODUCTION_MANIFEST",
        "assignment_id": ASSIGNMENT_ID,
        "base_seeds": list(BASE_SEEDS), "learned_arms": list(LEARNED_ARMS),
        "event_cells": list(EVENT_CELLS),
        "training_sizes": list(PRODUCTION_CONFIG.training_sizes),
        "held_out_size": PRODUCTION_CONFIG.held_out_size,
        "seen_schedules": ["S1", "S2"], "held_out_schedule": "S*",
        "training": {
            "updates": PRODUCTION_CONFIG.updates,
            "episodes_per_update": PRODUCTION_CONFIG.episodes_per_update,
            "ticks_per_episode": PRODUCTION_CONFIG.episode_ticks,
            "ppo_epochs": PRODUCTION_CONFIG.ppo_epochs,
            "minibatch_agent_event_rows": PRODUCTION_CONFIG.minibatch_agent_rows,
            "final_checkpoint_only": True,
        },
        "network": {
            "row_encoder": "27->64->64 SiLU",
            "actor": "masked DeepSets mean+sum -> 64 GRU -> 5 actions",
            "critic": "masked DeepSets mean+sum -> 64 GRU -> scalar",
            "trainable_parameter_counts": parameter_counts,
        },
        "evaluation": {
            "base_worlds_per_seed": 1280,
            "row_order_replicas": PRODUCTION_CONFIG.row_order_replicas,
            "joint_holdout_worlds_per_event_cell": PRODUCTION_CONFIG.joint_holdout_worlds_per_cell,
        },
        "ordinary_float_comparison": {
            "rtol": PRODUCTION_CONFIG.ordinary_rtol,
            "atol": PRODUCTION_CONFIG.ordinary_atol,
        },
        "engineering_resource_envelope": {
            "wall_seconds": PRODUCTION_CONFIG.wall_cap_seconds,
            "peak_rss_bytes": PRODUCTION_CONFIG.peak_rss_bytes,
        },
    }


def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise RecoveryRefused(f"cannot load required JSON {path}: {exc}") from exc


def _command_matches(command: object, terminal: Mapping[str, object], output_root: Path, result_path: Path) -> bool:
    if not isinstance(command, list) or len(command) != 8 or not all(isinstance(x, str) for x in command):
        return False
    if command[1:4] != ["-m", "experiments.candidates.variable_n_fleet_churn_b2.run", "exercise"]:
        return False
    if command[4] != "--output-root" or command[6] != "--result":
        return False
    interpreter = Path(command[0]).resolve()
    mandated = Path("C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe").resolve()
    cwd = Path(str(terminal.get("cwd", Path.cwd()))).resolve()
    terminal_output = (cwd / command[5]).resolve() if not Path(command[5]).is_absolute() else Path(command[5]).resolve()
    terminal_result = (cwd / command[7]).resolve() if not Path(command[7]).is_absolute() else Path(command[7]).resolve()
    return interpreter == mandated and terminal_output == output_root and terminal_result == result_path


def _parse_terminal(path: Path, output_root: Path, result_path: Path) -> tuple[dict[str, Any], datetime, datetime]:
    terminal = _load_json(path)
    if not isinstance(terminal, dict) or not TERMINAL_REQUIRED_KEYS.issubset(terminal):
        raise RecoveryRefused(f"original terminal JSON lacks required keys {sorted(TERMINAL_REQUIRED_KEYS)}")
    if not _command_matches(terminal["command"], terminal, output_root, result_path):
        raise RecoveryRefused("original terminal command does not exactly match the registered exercise command")
    if isinstance(terminal["exit_code"], bool) or not isinstance(terminal["exit_code"], int) or terminal["exit_code"] == 0:
        raise RecoveryRefused("original terminal must record a nonzero integer exit code")
    try:
        started = datetime.fromisoformat(terminal["started_at"])
        ended = datetime.fromisoformat(terminal["ended_at"])
    except (TypeError, ValueError) as exc:
        raise RecoveryRefused("original terminal timestamps must be ISO-8601 datetimes") from exc
    if started.tzinfo is None or ended.tzinfo is None or ended <= started:
        raise RecoveryRefused("original terminal must be timezone-aware and ended after it started")
    if bool(terminal.get("process_live", False)):
        raise RecoveryRefused("original terminal says the scientific process is still live")
    return terminal, started, ended


def _matching_processes(output_root: Path) -> list[dict[str, object]]:
    if os.name != "nt":
        raise RecoveryRefused("matching-process guard is implemented only for the registered Windows host")
    escaped_root = str(output_root).replace("'", "''")
    script = (
        "$selfPid=" + str(os.getpid()) + "; "
        "$needle='experiments.candidates.variable_n_fleet_churn_b2'; "
        "$root='" + escaped_root + "'; "
        "$rows=Get-CimInstance Win32_Process | Where-Object { $_.ProcessId -ne $selfPid -and $_.Name -match '^python(w)?\\.exe$' -and "
        "$_.CommandLine -and -not $_.CommandLine.Contains('hmasd_run_observed_command.py') -and "
        "$_.CommandLine.Contains($needle) -and $_.CommandLine.Contains($root) } | "
        "Select-Object ProcessId,CommandLine; if($rows){$rows | ConvertTo-Json -Compress}else{'[]'}"
    )
    completed = subprocess.run(
        ["powershell", "-NoProfile", "-NonInteractive", "-Command", script],
        capture_output=True, text=True, timeout=20, check=False,
    )
    if completed.returncode != 0:
        raise RecoveryRefused(f"cannot establish matching-process guard: {completed.stderr.strip()}")
    decoded = json.loads(completed.stdout.strip() or "[]")
    if isinstance(decoded, dict):
        decoded = [decoded]
    return decoded


def _checkpoint_contract(path: Path, arm: str, seed: int) -> tuple[RecurrentSetActorCritic | None, dict[str, object]]:
    if not path.is_file() or path.with_suffix(path.suffix + ".tmp").exists():
        return None, {"reusable": False, "reason": "absent_or_atomic_temporary_present", "path": str(path)}
    expected_model = RecurrentSetActorCritic()
    expected_state = expected_model.state_dict()
    expected_keys = {
        "schema", "arm", "base_seed", "update", "episodes", "model",
        "optimizer", "optimizer_steps", "parameter_count",
    }
    try:
        payload = torch.load(path, map_location="cpu", weights_only=True)
        if not isinstance(payload, dict) or set(payload) != expected_keys:
            raise ValueError("checkpoint schema keys are not exact")
        scalar_expected = {
            "schema": CHECKPOINT_SCHEMA, "arm": arm, "base_seed": seed,
            "update": 32, "episodes": 4096,
            "optimizer_steps": EXPECTED_OPTIMIZER_STEPS,
            "parameter_count": expected_model.parameter_count,
        }
        for key, expected in scalar_expected.items():
            if payload[key] != expected or type(payload[key]) is not type(expected):
                raise ValueError(f"{key} mismatch")
        state = payload["model"]
        if not isinstance(state, dict) or set(state) != set(expected_state):
            raise ValueError("model state keys mismatch")
        for key, expected_tensor in expected_state.items():
            tensor = state[key]
            if not isinstance(tensor, torch.Tensor) or tensor.shape != expected_tensor.shape or tensor.dtype != expected_tensor.dtype:
                raise ValueError(f"model tensor contract mismatch: {key}")
        expected_model.load_state_dict(state, strict=True)
        optimizer = torch.optim.Adam(
            expected_model.parameters(), lr=PRODUCTION_CONFIG.learning_rate,
            betas=(.9, .999), eps=1e-8, weight_decay=0.0,
        )
        optimizer.load_state_dict(payload["optimizer"])
        groups = optimizer.param_groups
        if len(groups) != 1 or groups[0]["lr"] != PRODUCTION_CONFIG.learning_rate or groups[0]["betas"] != (.9, .999):
            raise ValueError("optimizer state does not match the frozen Adam contract")
        expected_model.eval()
        return expected_model, {
            "reusable": True, "path": str(path), "schema": CHECKPOINT_SCHEMA,
            "arm": arm, "base_seed": seed, "update": 32, "episodes": 4096,
            "optimizer_steps": EXPECTED_OPTIMIZER_STEPS,
            "parameter_count": expected_model.parameter_count,
            "curves": "unavailable", "validation": "unavailable",
            "trajectory_or_validation_claim": False,
        }
    except Exception as exc:
        return None, {"reusable": False, "reason": f"contract_failure:{type(exc).__name__}:{exc}", "path": str(path)}


def _observed_projection(output_root: Path, original_started: datetime) -> dict[str, object]:
    previous = original_started.timestamp()
    train_seconds: list[float] = []
    evaluation_seconds: list[float] = []
    existing = 0
    for seed in BASE_SEEDS:
        for arm in LEARNED_ARMS:
            checkpoint = output_root / "checkpoints" / f"seed_{seed}" / f"{arm}.pt"
            if checkpoint.exists():
                stamp = checkpoint.stat().st_mtime
                if stamp > previous:
                    train_seconds.append(stamp - previous)
                previous = max(previous, stamp)
                existing += 1
        summary = output_root / "seed_summaries" / f"seed_{seed}.json"
        if summary.exists():
            stamp = summary.stat().st_mtime
            if stamp > previous:
                evaluation_seconds.append(stamp - previous)
            previous = max(previous, stamp)
    train_estimate = statistics.median(train_seconds) if train_seconds else 20 * 60.0
    eval_estimate = statistics.median(evaluation_seconds) if evaluation_seconds else 5 * 60.0
    return {
        "existing_checkpoint_files": existing,
        "observed_train_seconds": train_seconds,
        "observed_evaluation_seconds": evaluation_seconds,
        "estimated_train_seconds_each": train_estimate,
        "estimated_evaluation_seconds_each": eval_estimate,
    }


def _closure_labels(analysis: Mapping[str, object]) -> dict[str, object]:
    conditions = analysis["registered_support_conditions"]  # type: ignore[index]
    return {
        "review_revision": CLOSURE_REVISION,
        "inference_object": "complete coherent realized finite-panel trained-package endpoints",
        "condition_1_DE_and_DER": bool(conditions["D_E_material"] and conditions["D_ER_material"]),  # type: ignore[index]
        "condition_2_same_metric_C1_C2": {
            "met": bool(conditions["typed_vs_reset_same_metric_both_C1_C2"]),  # type: ignore[index]
            "same_metric_rule_enforced": True,
        },
        "condition_3_C3_operational_equivalence": bool(
            conditions["C3_J_practical_equivalence"] and conditions["C3_RR3_practical_equivalence"]  # type: ignore[index]
        ),
        "condition_4": {
            "available": False,
            "reason": "C2 SCR old-command semantics are not uniquely prespecified",
            "C2_SCR_label": "implementation-defined conditional diagnostic, non-claim-bearing",
            "hard_stale_error_count_component": bool(conditions["typed_hard_stale_errors_zero"]),  # type: ignore[index]
        },
        "condition_5_fresh_oracle_headroom": bool(conditions["fresh_oracle_room"]),  # type: ignore[index]
        "full_five_condition_conjunction": {"available": False, "met": None},
        "claim_exclusions": [
            "carrier-only causal effect", "global calibration", "population inference",
            "safety guarantee", "UAV performance", "arbitrary-N robustness",
            "adaptive-k capability", "learning-trajectory or validation behavior for reused checkpoints",
        ],
    }


class _Deadline:
    def __init__(self, started: datetime, reconstructed: int, evaluations: int, projection: Mapping[str, object]):
        self.deadline = started + timedelta(hours=8)
        self.remaining_train = reconstructed
        self.remaining_eval = evaluations
        self.train_observations = list(projection["observed_train_seconds"])  # type: ignore[arg-type]
        self.eval_observations = list(projection["observed_evaluation_seconds"])  # type: ignore[arg-type]
        self.train_default = float(projection["estimated_train_seconds_each"])
        self.eval_default = float(projection["estimated_evaluation_seconds_each"])

    def projected_seconds(self) -> float:
        train = statistics.median(self.train_observations) if self.train_observations else self.train_default
        evaluate = statistics.median(self.eval_observations) if self.eval_observations else self.eval_default
        return self.remaining_train * train + self.remaining_eval * evaluate

    def guard(self, boundary: str) -> None:
        now = datetime.now(self.deadline.tzinfo)
        remaining = (self.deadline - now).total_seconds()
        projected = self.projected_seconds()
        if peak_process_rss_bytes() > PRODUCTION_CONFIG.peak_rss_bytes:
            raise RecoveryRefused(f"registered peak-RSS envelope exceeded at {boundary}")
        if remaining <= 0 or projected > remaining:
            raise RecoveryRefused(
                f"cumulative deadline projection cannot fit at {boundary}: "
                f"remaining_seconds={remaining:.3f} projected_seconds={projected:.3f}"
            )


def recover(output_root: Path, result_path: Path, terminal_json: Path) -> dict[str, object]:
    output_root, result_path, terminal_json = output_root.resolve(), result_path.resolve(), terminal_json.resolve()
    recovery_root = output_root / "recovery_math_closure_20260812_01"
    marker = output_root / ".VNFC_B2_RECOVERY_ONCE.json"
    terminal_path = recovery_root / "recovery_terminal.json"
    if result_path.exists():
        raise RecoveryRefused("retained result must be absent before recovery")
    if marker.exists():
        raise RecoveryRefused(f"exact-once recovery marker already exists: {marker}")
    manifest_path = output_root / "manifest.json"
    if _load_json(manifest_path) != expected_manifest():
        raise RecoveryRefused("original treatment manifest is not the exact registered manifest")
    terminal, original_started, original_ended = _parse_terminal(terminal_json, output_root, result_path)
    if _matching_processes(output_root):
        raise RecoveryRefused("a matching VNFC-B2 scientific process is live")

    inspections: dict[str, dict[str, object]] = {}
    models: dict[int, dict[str, RecurrentSetActorCritic]] = {seed: {} for seed in BASE_SEEDS}
    missing: list[tuple[int, str]] = []
    for seed in BASE_SEEDS:
        for arm in LEARNED_ARMS:
            path = output_root / "checkpoints" / f"seed_{seed}" / f"{arm}.pt"
            model, facts = _checkpoint_contract(path, arm, seed)
            inspections[f"{seed}:{arm}"] = facts
            if model is None:
                missing.append((seed, arm))
            else:
                models[seed][arm] = model
    projection = _observed_projection(output_root, original_started)
    projection["contract_reusable_checkpoints"] = 24 - len(missing)
    projection["reconstructed_models_required"] = len(missing)
    projection["fresh_seed_evaluations_required"] = 8
    projection["projected_remaining_wall_seconds"] = (
        len(missing) * float(projection["estimated_train_seconds_each"])
        + 8 * float(projection["estimated_evaluation_seconds_each"])
    )
    deadline = _Deadline(original_started, len(missing), 8, projection)
    deadline.guard("pre_marker")
    recovery_started = datetime.now(original_started.tzinfo)
    _create_once(marker, {
        "artifact_kind": "VNFC_B2_EXACT_ONCE_RECOVERY_MARKER",
        "assignment_id": ASSIGNMENT_ID, "closure_revision": CLOSURE_REVISION,
        "original_started_at": original_started.isoformat(),
        "absolute_deadline": deadline.deadline.isoformat(),
        "recovery_started_at": recovery_started.isoformat(),
        "terminal_json": str(terminal_json), "projection": projection,
    })

    reconstructed_durations: list[float] = []
    evaluation_durations: list[float] = []
    seed_rows: list[dict[str, object]] = []
    try:
        for seed, arm in missing:
            deadline.guard(f"before_reconstruct:{seed}:{arm}")
            started = time.perf_counter()
            model, optimizer, curves = train_arm(arm, seed)
            duration = time.perf_counter() - started
            reconstructed_durations.append(duration)
            deadline.train_observations.append(duration)
            deadline.remaining_train -= 1
            path = recovery_root / "checkpoints" / f"seed_{seed}" / f"{arm}.pt"
            save_checkpoint(path, model, optimizer, arm, seed, curves)
            checked, facts = _checkpoint_contract(path, arm, seed)
            if checked is None:
                raise RecoveryRefused(f"reconstructed checkpoint failed its exact contract: {seed}:{arm}:{facts}")
            facts.update({"reconstructed": True, "curves": curves, "validation": "not_run_reporting_only"})
            inspections[f"{seed}:{arm}"] = facts
            models[seed][arm] = checked
            deadline.guard(f"after_reconstruct:{seed}:{arm}")

        for seed in BASE_SEEDS:
            deadline.guard(f"before_fresh_evaluation:{seed}")
            started = time.perf_counter()
            raw_path = recovery_root / "evaluation_rows" / f"seed_{seed}.jsonl.gz"
            evaluation = evaluate_models(models[seed], seed, raw_path)
            duration = time.perf_counter() - started
            evaluation_durations.append(duration)
            deadline.eval_observations.append(duration)
            deadline.remaining_eval -= 1
            seed_row = {
                "base_seed": seed, "arms": evaluation["arms"],
                "inference_latency": evaluation["inference_latency"],
                "learning_curves": {
                    arm: inspections[f"{seed}:{arm}"].get("curves", "unavailable") for arm in LEARNED_ARMS
                },
                "validation": {
                    arm: inspections[f"{seed}:{arm}"].get("validation", "unavailable") for arm in LEARNED_ARMS
                },
                "training_wall_seconds": {
                    arm: None if inspections[f"{seed}:{arm}"].get("reusable") else None for arm in LEARNED_ARMS
                },
                "base_worlds": evaluation["base_worlds"],
                "replicated_episodes_per_arm": evaluation["replicated_episodes_per_arm"],
                "raw_rows": str(raw_path), "evaluation_version": CLOSURE_REVISION,
            }
            seed_rows.append(seed_row)
            _atomic_json(recovery_root / "seed_summaries" / f"seed_{seed}.json", seed_row)
            deadline.guard(f"after_fresh_evaluation:{seed}")

        analysis = analyze(seed_rows)
        result = {
            "artifact_kind": "VNFC_B2_RECOVERED_RETAINED_RESULT",
            "assignment_id": ASSIGNMENT_ID, "closure_revision": CLOSURE_REVISION,
            "evaluation_version": CLOSURE_REVISION,
            "original_terminal": terminal,
            "original_resource_fact": {
                "started_at": original_started.isoformat(), "ended_at": original_ended.isoformat(),
                "exit_code": terminal["exit_code"],
                "original_wall_seconds": (original_ended - original_started).total_seconds(),
                "original_three_hour_envelope_met": False,
            },
            "cumulative_deadline": deadline.deadline.isoformat(),
            "checkpoint_inspection": inspections,
            "projection": projection,
            "recovery_resources": {
                "reconstructed_arm_seconds": reconstructed_durations,
                "fresh_evaluation_seconds": evaluation_durations,
                "peak_rss_bytes": peak_process_rss_bytes(),
                "finished_at": datetime.now(original_started.tzinfo).isoformat(),
            },
            "historical_rows_or_summaries_reused": False,
            "fresh_coherent_seed_rows": seed_rows,
            "analysis": analysis,
            "mathematical_closure_labels": _closure_labels(analysis),
            "claim_ceiling": (
                "Realized finite-panel endpoint comparisons of the independently trained named packages "
                "at the registered N=5,S* point only; no causal, global-calibration, population, safety, "
                "UAV, arbitrary-N, or adaptive-k claim."
            ),
        }
        _atomic_json(recovery_root / "raw_result.json", result)
        _atomic_json(result_path, result)
        _atomic_json(terminal_path, {
            "artifact_kind": "VNFC_B2_RECOVERY_TERMINAL", "completed": True,
            "result": str(result_path), "finished_at": datetime.now(original_started.tzinfo).isoformat(),
            "absolute_deadline": deadline.deadline.isoformat(),
        })
        return result
    except Exception as exc:
        _atomic_json(terminal_path, {
            "artifact_kind": "VNFC_B2_RECOVERY_TERMINAL", "completed": False,
            "error_type": type(exc).__name__, "error": str(exc),
            "finished_at": datetime.now(original_started.tzinfo).isoformat(),
            "absolute_deadline": deadline.deadline.isoformat(),
            "remaining_reconstructions": deadline.remaining_train,
            "remaining_fresh_seed_evaluations": deadline.remaining_eval,
            "projected_remaining_seconds": deadline.projected_seconds(),
        })
        raise


def validate_recovery_source(output_root: Path | None = None) -> dict[str, object]:
    model = RecurrentSetActorCritic()
    report: dict[str, object] = {
        "assignment_id": ASSIGNMENT_ID, "closure_revision": CLOSURE_REVISION,
        "checkpoint_schema": CHECKPOINT_SCHEMA,
        "expected_optimizer_steps": EXPECTED_OPTIMIZER_STEPS,
        "model_parameter_count": model.parameter_count,
        "manifest": expected_manifest(),
        "recovery_order": [[seed, arm] for seed in BASE_SEEDS for arm in LEARNED_ARMS],
        "fresh_evaluation_models": len(BASE_SEEDS) * len(LEARNED_ARMS),
        "historical_rows_or_summaries_reused": False,
        "deadline_rule": "original_started_at_plus_8_hours_never_reset",
    }
    if output_root is not None:
        output_root = output_root.resolve()
        manifest_exact = _load_json(output_root / "manifest.json") == expected_manifest()
        checkpoints = {}
        reusable = 0
        for seed in BASE_SEEDS:
            for arm in LEARNED_ARMS:
                _, facts = _checkpoint_contract(
                    output_root / "checkpoints" / f"seed_{seed}" / f"{arm}.pt", arm, seed,
                )
                checkpoints[f"{seed}:{arm}"] = facts
                reusable += int(bool(facts["reusable"]))
        report.update({
            "manifest_exact": manifest_exact, "checkpoint_contracts": checkpoints,
            "reusable_final_checkpoints": reusable, "missing_or_nonreusable": 24 - reusable,
        })
    return report
