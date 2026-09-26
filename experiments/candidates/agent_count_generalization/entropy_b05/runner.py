"""Two fixed B05 SET fits comparing low-level entropy coefficients .05 and zero."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import resource
import sys
import time
import traceback
from typing import Any, Callable

import numpy as np
import torch

from experiments.candidates.agent_count_generalization.adapter import make_envs
from experiments.candidates.agent_count_generalization.configuration import (
    DEFAULT_SPEC,
    DIRECTION,
    FitSpec,
    config_dict,
    make_config,
)
from experiments.candidates.agent_count_generalization.entropy_b04 import runner as b04
from experiments.candidates.agent_count_generalization.models import build_agent, strict_sync
from experiments.candidates.agent_count_generalization.runner import (
    COMPONENTS,
    capture_parameters,
    digest_agent,
    finite,
    jsonable,
    model_modules,
    native_components,
    optimizer_counts,
    parameter_motion,
    preserve_rng,
    reset_all,
    save_checkpoint,
    seed_rng,
    write_json,
)


OBJECT_ID = "s1_entropy_b05"
EVALUATION_SEED_BASE = 1_500_000


@dataclass(frozen=True)
class TrainingCell:
    index: int
    key: str
    arm: str
    law: str
    seed: int
    tag: str
    lambda_l: float


CELLS = (
    TrainingCell(1, "set_l05", "SET", "clip", 953201,
                 "s1_entropy_b05_set_l05_s953201", .05),
    TrainingCell(2, "set_l0", "SET", "clip", 953201,
                 "s1_entropy_b05_set_l0_s953201", 0.0),
)
CELL_BY_KEY = {cell.key: cell for cell in CELLS}


@dataclass(frozen=True)
class ControlBinding:
    """Explicit byte identity of the completed first B05 cell."""

    path: Path
    sha256: str


def make_b05_config(cell: TrainingCell, envs: list[Any], spec: FitSpec) -> Any:
    config = make_config(cell.arm, envs, cell.seed, spec)
    config.lambda_l = cell.lambda_l
    config.lambda_l_initial = cell.lambda_l
    config.lambda_l_final = cell.lambda_l
    config.use_entropy_annealing = False
    config.use_entropy_targets = False
    config.validate_config()
    return config


def b05_config_dict(config: Any) -> dict[str, Any]:
    result = config_dict(config)
    result.update(
        lambda_l_initial=float(config.lambda_l_initial),
        lambda_l_final=float(config.lambda_l_final),
        use_entropy_annealing=bool(config.use_entropy_annealing),
        use_entropy_targets=bool(config.use_entropy_targets),
    )
    return result


def _assert_config_contract(config: Any, cell: TrainingCell, *, expected_n: int = 6) -> None:
    coefficient = float(cell.lambda_l)
    if any(float(value) != coefficient for value in (
        config.lambda_l, config.lambda_l_initial, config.lambda_l_final,
    )):
        raise ValueError("B05 low-level entropy coefficient/endpoints changed")
    if bool(config.use_entropy_targets) or bool(config.use_entropy_annealing):
        raise ValueError("B05 entropy targets and annealing must remain disabled")
    if str(getattr(config, "continuous_action_distribution", "gaussian")) != "gaussian":
        raise ValueError("B05 must retain the raw Gaussian action distribution")
    if int(config.k) != 10 or int(config.n_agents) != expected_n:
        raise ValueError(f"B05 requires N{expected_n} and k10 for this phase")
    if str(config.count_arm) != "SET" or cell.arm != "SET" or cell.law != "clip":
        raise ValueError("B05 requires the fixed SET clipped-execution package")


def assert_agent_entropy_contract(agent: Any, cell: TrainingCell) -> dict[str, Any]:
    result = {
        "config_lambda_l": float(agent.config.lambda_l),
        "effective_lambda_l": float(agent.low_level_entropy_coef),
        "lambda_l_initial": float(agent.config.lambda_l_initial),
        "lambda_l_final": float(agent.config.lambda_l_final),
        "entropy_targets_enabled": bool(agent.use_entropy_targets),
        "entropy_annealing_enabled": bool(agent.use_entropy_annealing),
    }
    expected = {
        "config_lambda_l": cell.lambda_l,
        "effective_lambda_l": cell.lambda_l,
        "lambda_l_initial": cell.lambda_l,
        "lambda_l_final": cell.lambda_l,
        "entropy_targets_enabled": False,
        "entropy_annealing_enabled": False,
    }
    if result != expected:
        raise ValueError("B05 effective low-level entropy treatment changed")
    return result


def _panel_world_seed(rollout: int, n: int) -> int:
    return EVALUATION_SEED_BASE + 1000 * rollout + 100 * n


def _expected_counts(spec: FitSpec) -> dict[str, int]:
    return {
        "training_team_steps": spec.rollouts * spec.train_lanes * spec.horizon,
        "stored_team_steps": spec.rollouts * spec.train_lanes * spec.horizon,
        "training_episodes": spec.rollouts * spec.train_lanes,
        "terminal_resets": spec.rollouts * spec.train_lanes,
        "updates": spec.rollouts,
        "evaluation_team_steps": (
            len(spec.panels) * len(spec.test_ns) * spec.eval_lanes * spec.horizon
        ),
        "evaluation_episodes": len(spec.panels) * len(spec.test_ns) * spec.eval_lanes,
    }


def _expected_set_optimizer_calls(spec: FitSpec, *, rollouts: int | None = None) -> dict[str, int]:
    chunks_per_trajectory = max(1, spec.horizon // 10)
    sequences = spec.train_lanes * spec.train_n * chunks_per_trajectory
    batches_per_epoch = (sequences + spec.sequence_batch_size - 1) // spec.sequence_batch_size
    updates = spec.rollouts if rollouts is None else rollouts
    actor_critic = updates * spec.ppo_epochs * batches_per_epoch
    return {
        "coordinator": 0,
        "discoverer_actor": actor_critic,
        "discoverer_critic": actor_critic,
        "team_discriminator": 0,
        "individual_discriminator": 0,
    }


def _expected_panel_worlds(spec: FitSpec) -> dict[tuple[int, int], list[int]]:
    return {
        (int(rollout), int(n)): list(range(
            _panel_world_seed(int(rollout), int(n)),
            _panel_world_seed(int(rollout), int(n)) + spec.eval_lanes,
        ))
        for rollout in spec.panels for n in spec.test_ns
    }


def _control_panel_payload_valid(
    row: dict[str, Any], *, rollout: int, n: int, spec: FitSpec,
    training_config: dict[str, Any],
) -> bool:
    try:
        if (
            row.get("status") != "complete"
            or row.get("after_rollout") != rollout
            or row.get("training_team_steps") != rollout * spec.train_lanes * spec.horizon
            or row.get("test_n") != n
            or row.get("execution_law") != "clip"
            or row.get("steps") != spec.eval_lanes * spec.horizon
            or row.get("episodes") != spec.eval_lanes
            or row.get("optimizer_calls") != _expected_set_optimizer_calls(spec, rollouts=0)
            or row.get("frozen_weights_and_normalizers") is not True
        ):
            return False
        bounds = row["executed_action_bounds"]
        low, high = float(bounds["minimum"]), float(bounds["maximum"])
        if not np.isfinite((low, high)).all() or low < -1.0 or high > 1.0 or low > high:
            return False
        j = np.asarray(row["J"], dtype=np.float64)
        returns = np.asarray(row["scalar_returns"], dtype=np.float64)
        components = row["component_means"]
        if set(components) != set(COMPONENTS):
            return False
        arrays = {name: np.asarray(components[name], dtype=np.float64) for name in COMPONENTS}
        expected_shape = (spec.eval_lanes,)
        if j.shape != expected_shape or returns.shape != expected_shape:
            return False
        if any(values.shape != expected_shape for values in arrays.values()):
            return False
        if not all(np.isfinite(values).all() for values in (j, returns, *arrays.values())):
            return False
        native = .7 * arrays["coverage_reward"] + .3 * arrays["quality_reward"] - arrays[
            "energy_penalty"
        ]
        if not np.allclose(j, n * returns / spec.horizon, atol=1e-7, rtol=1e-6):
            return False
        if not np.allclose(j, arrays["total_reward"], atol=1e-7, rtol=1e-6):
            return False
        if not np.allclose(native, arrays["total_reward"], atol=1e-7, rtol=1e-6):
            return False
        panel_config = row["config"]
        allowed = {
            "n_agents", "n_uavs", "num_envs", "batch_size", "discriminator_batch_size",
        }
        if any(
            panel_config.get(key) != value
            for key, value in training_config.items() if key not in allowed
        ):
            return False
        expected_batch_numerator = (
            int(training_config["batch_size"]) * n * spec.eval_lanes
        )
        expected_batch_denominator = spec.train_n * spec.train_lanes
        if expected_batch_numerator % expected_batch_denominator:
            return False
        expected_batch = expected_batch_numerator // expected_batch_denominator
        if (
            panel_config.get("n_agents") != n
            or panel_config.get("n_uavs") != n
            or panel_config.get("num_envs") != spec.eval_lanes
            or panel_config.get("batch_size") != expected_batch
            or panel_config.get("discriminator_batch_size") != expected_batch
        ):
            return False
    except (KeyError, TypeError, ValueError):
        return False
    return True


def _read_control(
    binding: ControlBinding, candidate: TrainingCell, launch_sha: str,
    spec: FitSpec, record: dict[str, Any],
) -> dict[str, Any]:
    record.update(
        required=True, path=str(binding.path), expected_sha256=binding.sha256,
        expected_launch_sha=launch_sha, expected_object_id=OBJECT_ID,
        expected_tag=CELLS[0].tag, expected_cell_key=CELLS[0].key,
    )
    if candidate.key != "set_l0":
        raise ValueError("B05 control binding is valid only for the fixed zero cell")
    if len(binding.sha256) != 64 or any(ch not in "0123456789abcdef" for ch in binding.sha256):
        raise ValueError("B05 control SHA-256 must be 64 lowercase hexadecimal characters")
    payload = binding.path.read_bytes()
    observed_sha = hashlib.sha256(payload).hexdigest()
    record["observed_sha256"] = observed_sha
    record["summary_bytes_match"] = observed_sha == binding.sha256
    if not record["summary_bytes_match"]:
        raise ValueError("B05 control summary SHA-256 mismatch")
    control = json.loads(payload)
    first = CELLS[0]
    identity = {
        "status": control.get("status"),
        "object_id": control.get("object_id"),
        "launch_sha": control.get("launch_sha"),
        "tag": control.get("tag"),
        "arm": control.get("arm"),
        "training_action_law": control.get("training_action_law"),
        "seed": control.get("seed"),
        "cell_key": control.get("cell", {}).get("key"),
        "cell_tag": control.get("cell", {}).get("tag"),
        "cell_lambda_l": control.get("cell", {}).get("lambda_l"),
    }
    expected_identity = {
        "status": "complete", "object_id": OBJECT_ID, "launch_sha": launch_sha,
        "tag": first.tag, "arm": first.arm, "training_action_law": first.law,
        "seed": first.seed, "cell_key": first.key, "cell_tag": first.tag,
        "cell_lambda_l": first.lambda_l,
    }
    record["observed_identity"] = identity
    record["identity_match"] = identity == expected_identity
    if not record["identity_match"]:
        raise ValueError("B05 control status/source/object/cell identity mismatch")
    record["spec_match"] = control.get("spec") == jsonable(vars(spec))
    record["evaluation_seed_base_match"] = (
        control.get("evaluation_seed_base") == EVALUATION_SEED_BASE
    )
    record["training_worlds_match"] = control.get("training_world_seeds") == list(
        range(first.seed, first.seed + spec.train_lanes)
    )
    record["counts_match"] = control.get("counts") == _expected_counts(spec)
    if not all(record[name] for name in (
        "spec_match", "evaluation_seed_base_match", "training_worlds_match", "counts_match",
    )):
        raise ValueError("B05 control spec/world/count contract mismatch")
    config = control.get("config", {})
    expected_worlds = _expected_panel_worlds(spec)
    observed_worlds = {}
    panels_complete = True
    panel_payloads_valid = True
    for row in control.get("panels", []):
        try:
            key = (int(row["after_rollout"]), int(row["test_n"]))
        except (KeyError, TypeError, ValueError):
            panels_complete = False
            continue
        if key in observed_worlds:
            panels_complete = False
        observed_worlds[key] = row.get("world_seeds")
        panels_complete &= row.get("status") == "complete"
        panel_payloads_valid &= _control_panel_payload_valid(
            row, rollout=key[0], n=key[1], spec=spec, training_config=config,
        )
    record["panel_worlds_match"] = panels_complete and observed_worlds == expected_worlds
    record["panel_payloads_valid"] = panel_payloads_valid and set(observed_worlds) == set(
        expected_worlds
    )
    record["rollout_count_match"] = len(control.get("rollouts", [])) == spec.rollouts
    record["checkpoint_count_match"] = len(control.get("checkpoints", [])) == len(spec.panels)
    optimizer_calls = control.get("optimizer_calls", {})
    record["optimizer_contract_match"] = optimizer_calls == _expected_set_optimizer_calls(spec)
    rollout_optimizer_match = True
    for index, row in enumerate(control.get("rollouts", []), start=1):
        expected_delta = _expected_set_optimizer_calls(spec, rollouts=1)
        expected_total = _expected_set_optimizer_calls(spec, rollouts=index)
        returns = np.asarray(row.get("training_scalar_returns", []), dtype=np.float64)
        rollout_optimizer_match &= (
            row.get("rollout") == index
            and row.get("team_steps") == index * spec.train_lanes * spec.horizon
            and row.get("optimizer_delta") == expected_delta
            and row.get("optimizer_total") == expected_total
            and returns.shape == (spec.train_lanes,)
            and bool(np.isfinite(returns).all())
            and row.get("action_motion_telemetry", {}).get("team_steps")
            == spec.train_lanes * spec.horizon
        )
    record["rollout_optimizer_totals_match"] = rollout_optimizer_match
    if not all(record[name] for name in (
        "panel_worlds_match", "panel_payloads_valid", "rollout_count_match",
        "checkpoint_count_match", "optimizer_contract_match", "rollout_optimizer_totals_match",
    )):
        raise ValueError("B05 control panels/rollouts/checkpoints/optimizer contract incomplete")
    record["control_entropy_config_match"] = (
        config.get("lambda_l") == .05
        and config.get("lambda_l_initial") == .05
        and config.get("lambda_l_final") == .05
        and config.get("use_entropy_annealing") is False
        and config.get("use_entropy_targets") is False
    )
    digest = control.get("observed_initial_parameter_normalizer_digest")
    record["control_initial_digest"] = digest
    record["control_initial_digest_well_formed"] = (
        isinstance(digest, str) and len(digest) == 64
        and all(ch in "0123456789abcdef" for ch in digest)
    )
    if not record["control_entropy_config_match"] or not record[
        "control_initial_digest_well_formed"
    ]:
        raise ValueError("B05 control entropy config or initial digest invalid")
    return control


_TREATMENT_CONFIG_FIELDS = {
    "lambda_l", "lambda_l_initial", "lambda_l_final",
}


def _compare_control_config(
    candidate: dict[str, Any], control: dict[str, Any], record: dict[str, Any],
) -> None:
    old = control.get("config", {})
    all_keys = set(old) | set(candidate)
    differing = {
        key: {"control_l05": old.get(key), "candidate_l0": candidate.get(key)}
        for key in sorted(all_keys - _TREATMENT_CONFIG_FIELDS)
        if candidate.get(key) != old.get(key)
    }
    record["config_differences_excluding_declared_coefficient_fields"] = differing
    record["declared_coefficient_fields"] = {
        key: {"control_l05": old.get(key), "candidate_l0": candidate.get(key)}
        for key in sorted(_TREATMENT_CONFIG_FIELDS)
    }
    expected = all(old.get(key) == .05 and candidate.get(key) == 0.0
                   for key in _TREATMENT_CONFIG_FIELDS)
    record["config_match_apart_from_declared_coefficient_fields"] = not differing and expected
    if not record["config_match_apart_from_declared_coefficient_fields"]:
        raise ValueError("B05 control/candidate config differs outside fixed coefficient")


_INITIAL_PANEL_FIELDS = (
    "after_rollout", "training_team_steps", "test_n", "world_seeds",
    "execution_law", "status", "steps", "episodes", "J", "scalar_returns",
    "component_means", "optimizer_calls", "frozen_weights_and_normalizers",
    "executed_action_bounds",
)


def _initial_panel_evidence(summary: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {key: row[key] for key in _INITIAL_PANEL_FIELDS}
        for row in summary.get("panels", []) if row.get("after_rollout") == 0
    ]


def _first_collection_evidence(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "training_scalar_returns": row["training_scalar_returns"],
        "action_motion_telemetry": row["action_motion_telemetry"],
        "raw_sigma_before_update": row["raw_sigma_before_update"],
        "raw_log_sigma_before_update": row["raw_log_sigma_before_update"],
        "analytic_raw_entropy_before_update": row["analytic_raw_entropy_before_update"],
    }


def _require_pre_update_control_match(
    summary: dict[str, Any], control: dict[str, Any], record: dict[str, Any],
) -> None:
    initial_match = _initial_panel_evidence(summary) == _initial_panel_evidence(control)
    active = summary["_active_training_rollout"]
    observed = {
        "training_scalar_returns": active["scalar_returns"],
        "action_motion_telemetry": active["action_motion_telemetry"],
        "raw_sigma_before_update": active["raw_sigma_before_update"],
        "raw_log_sigma_before_update": active["raw_log_sigma_before_update"],
        "analytic_raw_entropy_before_update": active["analytic_raw_entropy_before_update"],
    }
    expected = _first_collection_evidence(control["rollouts"][0])
    record["initial_per_world_outputs_match"] = initial_match
    record["first_pre_update_collection_match"] = observed == expected
    record["pre_update_match"] = initial_match and observed == expected
    if not record["pre_update_match"]:
        raise ValueError("B05 initial evaluation or first pre-update collection mismatch")


def build_control_comparisons(
    summary: dict[str, Any], control: dict[str, Any], spec: FitSpec,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    controls = {
        (int(row["after_rollout"]), int(row["test_n"])): row
        for row in control["panels"] if row.get("status") == "complete"
    }
    comparisons = []
    for candidate in summary["panels"]:
        key = (int(candidate["after_rollout"]), int(candidate["test_n"]))
        old = controls.get(key)
        if candidate.get("status") != "complete" or old is None:
            raise ValueError(f"B05 missing complete matched control panel {key}")
        if candidate["world_seeds"] != old["world_seeds"]:
            raise ValueError(f"B05 candidate/control world mismatch at panel {key}")
        candidate_j = np.asarray(candidate["J"], dtype=np.float64)
        control_j = np.asarray(old["J"], dtype=np.float64)
        if candidate_j.shape != control_j.shape:
            raise ValueError(f"B05 candidate/control J width mismatch at panel {key}")
        component_rows = {}
        for name in COMPONENTS:
            zero = np.asarray(candidate["component_means"][name], dtype=np.float64)
            l05 = np.asarray(old["component_means"][name], dtype=np.float64)
            if zero.shape != l05.shape:
                raise ValueError(f"B05 candidate/control {name} width mismatch at panel {key}")
            delta = zero - l05
            component_rows[name] = {
                "set_l0_per_world": zero.tolist(),
                "set_l05_control_per_world": l05.tolist(),
                "set_l0_minus_set_l05_per_world": delta.tolist(),
                "set_l0_minus_set_l05_mean": float(delta.mean()),
            }
        delta_j = candidate_j - control_j
        comparisons.append({
            "after_rollout": key[0], "test_n": key[1],
            "world_seeds": candidate["world_seeds"],
            "set_l0_J_per_world": candidate_j.tolist(),
            "set_l05_control_J_per_world": control_j.tolist(),
            "E_J_set_l0_minus_set_l05_per_world": delta_j.tolist(),
            "E_J_set_l0_minus_set_l05_mean": float(delta_j.mean()),
            "positive_world_count": int(np.count_nonzero(delta_j > 0)),
            "zero_world_count": int(np.count_nonzero(delta_j == 0)),
            "negative_world_count": int(np.count_nonzero(delta_j < 0)),
            "component_comparisons": component_rows,
        })
    if len(comparisons) != len(spec.panels) * len(spec.test_ns):
        raise ValueError("B05 control comparison panel count incomplete")
    final_rollout = max(map(int, spec.panels))
    final_rows = {
        int(row["test_n"]): row for row in comparisons
        if int(row["after_rollout"]) == final_rollout
    }
    if set(final_rows) != set(map(int, spec.test_ns)):
        raise ValueError("B05 final control comparison N panel incomplete")
    by_n = {}
    for n in sorted(final_rows):
        row = final_rows[n]
        by_n[str(n)] = {
            "E_J_set_l0_minus_set_l05_mean": row["E_J_set_l0_minus_set_l05_mean"],
            "delta_coverage_set_l0_minus_set_l05_mean": row[
                "component_comparisons"
            ]["coverage_reward"]["set_l0_minus_set_l05_mean"],
            "world_signs": {
                "positive": row["positive_world_count"],
                "zero": row["zero_world_count"],
                "negative": row["negative_world_count"],
            },
        }
    final = {
        "after_rollout": final_rollout,
        "by_test_n": by_n,
        "E_U_equal_weight_N4_N8": float(np.mean([
            final_rows[n]["E_J_set_l0_minus_set_l05_mean"] for n in (4, 8)
        ])) if 4 in final_rows and 8 in final_rows else None,
        "n6_no_observed_J_or_coverage_cost": (
            by_n["6"]["E_J_set_l0_minus_set_l05_mean"] >= 0
            and by_n["6"]["delta_coverage_set_l0_minus_set_l05_mean"] >= 0
        ) if "6" in by_n else None,
        "scope": "fresh within-SET set_l0 minus set_l05; no H6 or Q comparison",
    }
    return jsonable(comparisons), jsonable(final)


def _pool_motion(rows: list[dict[str, Any]]) -> dict[str, Any]:
    rate_fields = (
        "raw_coordinate_violations", "raw_uav_violations", "raw_team_step_violations",
        "boundary_truncated_coordinates", "boundary_visited_coordinates",
    )
    result: dict[str, Any] = {
        "rollout_count": len(rows),
        "team_steps": sum(int(row["action_motion_telemetry"]["team_steps"]) for row in rows),
    }
    for name in rate_fields:
        records = [row["action_motion_telemetry"][name] for row in rows]
        numerator = sum(int(value["numerator"]) for value in records)
        denominator = sum(int(value["denominator"]) for value in records)
        result[name] = {
            "numerator": numerator, "denominator": denominator,
            "rate": float(numerator / denominator) if denominator else None,
        }
    for name in (
        "raw_excess_sum", "raw_attempted_l2_sum", "executed_attempted_l2_sum",
        "realized_l2_sum",
    ):
        result[name] = float(sum(row["action_motion_telemetry"][name] for row in rows))
    result["raw_excess_max"] = (
        max(float(row["action_motion_telemetry"]["raw_excess_max"]) for row in rows)
        if rows else None
    )
    return result


def pooled_motion(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "full_rollouts_1_through_45": _pool_motion(rows),
        "late_rollouts_31_through_45": _pool_motion([
            row for row in rows if 31 <= int(row["rollout"]) <= 45
        ]),
    }


def evaluate_panel(
    learner: Any, cell: TrainingCell, rollout: int, out: Path,
    summary: dict[str, Any], spec: FitSpec, publish: Callable[[str], None],
) -> None:
    learner_model_before = digest_agent(learner)
    learner_runtime_before = b04.runtime_state_digest(learner)
    learner_rng_before = b04._rng_digest()
    with preserve_rng():
        for n in spec.test_ns:
            world_seed = _panel_world_seed(rollout, n)
            seed_rng(world_seed + 51)
            envs = make_envs(spec.eval_lanes, world_seed, n, spec.horizon)
            target, hooks = None, []
            row = {
                "after_rollout": rollout,
                "training_team_steps": rollout * spec.train_lanes * spec.horizon,
                "test_n": n,
                "world_seeds": list(range(world_seed, world_seed + spec.eval_lanes)),
                "execution_law": "clip", "status": "running", "steps": 0, "episodes": 0,
            }
            summary["panels"].append(row)
            publish(f"evaluation {rollout} N={n} starting")
            try:
                config = make_b05_config(cell, envs, spec)
                _assert_config_contract(config, cell, expected_n=n)
                target = build_agent(config, str(out / "evaluation_logs" / f"r{rollout}_n{n}"))
                assert_agent_entropy_contract(target, cell)
                strict_sync(target, learner)
                target.train(False)
                for lane in range(spec.eval_lanes):
                    target.reset_env_state(lane)
                calls, hooks = optimizer_counts(target)
                target_before = digest_agent(target)
                states, observations = reset_all(envs)
                steps = np.zeros(spec.eval_lanes, dtype=np.int64)
                dones = np.zeros(spec.eval_lanes, dtype=bool)
                returns = np.zeros(spec.eval_lanes, dtype=np.float64)
                components = {
                    name: np.zeros(spec.eval_lanes, dtype=np.float64) for name in COMPONENTS
                }
                executed_min, executed_max = float("inf"), float("-inf")
                with torch.no_grad():
                    for t in range(spec.horizon):
                        raw_actions, _, data = target.step(
                            states, observations, steps, dones, deterministic=True,
                            return_step_data=True, build_infos=False,
                        )
                        finite((raw_actions, data), "B05 evaluation policy output")
                        raw_before = raw_actions.copy()
                        executed = b04.map_training_actions(raw_actions, "clip")
                        if not np.array_equal(raw_actions, raw_before):
                            raise ValueError("B05 evaluation mapping mutated policy actions")
                        executed_min = min(executed_min, float(executed.min()))
                        executed_max = max(executed_max, float(executed.max()))
                        for lane, env in enumerate(envs):
                            obs, reward, term, trunc, info = env.step(executed[lane])
                            done = bool(term or trunc)
                            row["steps"] += 1
                            row["episodes"] += int(done)
                            summary["counts"]["evaluation_team_steps"] += 1
                            summary["counts"]["evaluation_episodes"] += int(done)
                            parts = native_components(info, reward, n)
                            returns[lane] += reward
                            for name in COMPONENTS:
                                components[name][lane] += parts[name]
                            states[lane], observations[lane], dones[lane] = info["next_state"], obs, done
                        steps += 1
                        if dones.any() and (t != spec.horizon - 1 or not dones.all()):
                            raise ValueError("unexpected B05 evaluation terminal boundary")
                if not dones.all():
                    raise ValueError("B05 evaluation missed fixed terminal boundary")
                j = n * returns / spec.horizon
                means = {name: values / spec.horizon for name, values in components.items()}
                if not np.allclose(j, means["total_reward"], atol=1e-7, rtol=1e-6):
                    raise ValueError("B05 evaluation native J/component identity failed")
                if any(calls.values()) or digest_agent(target) != target_before:
                    raise ValueError("B05 evaluation modified target parameters/normalizers")
                row.update(
                    status="complete", J=j.tolist(), scalar_returns=returns.tolist(),
                    component_means=jsonable(means), optimizer_calls=calls.copy(),
                    frozen_weights_and_normalizers=True,
                    executed_action_bounds={"minimum": executed_min, "maximum": executed_max},
                    config=b05_config_dict(config),
                )
                write_json(out / f"panel_{rollout:02d}_n{n}.json", row)
                publish(f"evaluation {rollout} N={n} complete")
            except Exception as exc:
                row.update(status="failed", failure=f"{type(exc).__name__}: {exc}")
                write_json(out / f"panel_{rollout:02d}_n{n}.json", row)
                raise
            finally:
                for hook in hooks:
                    hook.remove()
                for env in envs:
                    env.close()
                del target
    if digest_agent(learner) != learner_model_before:
        raise ValueError("B05 evaluation modified learner parameters/normalizers")
    if b04.runtime_state_digest(learner) != learner_runtime_before:
        raise ValueError("B05 evaluation modified learner runtime state")
    if b04._rng_digest() != learner_rng_before:
        raise ValueError("B05 evaluation modified learner/global RNG state")


def run_fit(
    out: Path, cell: TrainingCell, launch_sha: str, admission: dict[str, Any],
    spec: FitSpec = DEFAULT_SPEC, *, command_start: float | None = None,
    control_binding: ControlBinding | None = None,
    agent_setup_hook: Callable[[Any], None] | None = None,
    training_step_hook: Callable[[dict[str, Any]], None] | None = None,
) -> int:
    out = Path(out)
    if out.name != cell.tag:
        raise ValueError(f"B05 output basename must be fixed tag {cell.tag}")
    if (out / "summary.json").exists():
        raise ValueError("existing B05 scientific summary; reconcile original attempt")
    if 0 not in spec.panels:
        raise ValueError("B05 requires the initial evaluation panel for pair binding")
    if (cell.key == "set_l0") != (control_binding is not None):
        raise ValueError("B05 zero cell requires one control binding; .05 cell rejects one")
    out.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    if command_start is None:
        command_start = started
    summary: dict[str, Any] = {
        "schema": 1, "object_id": OBJECT_ID, "direction": DIRECTION,
        "cell": jsonable(vars(cell)), "arm": cell.arm, "training_action_law": cell.law,
        "seed": cell.seed, "tag": cell.tag, "launch_sha": launch_sha, "admission": admission,
        "status": "initializing", "fit_started": False, "failure": None,
        "spec": jsonable(vars(spec)), "panels": [], "checkpoints": [], "rollouts": [],
        "control_comparisons": [], "final_control_comparison": None,
        "control_binding": {"required": cell.key == "set_l0"},
        "counts": {name: 0 for name in _expected_counts(spec)},
        "training_world_seeds": list(range(cell.seed, cell.seed + spec.train_lanes)),
        "evaluation_action_law": "clip",
        "transition_indexing": (
            "action[t] and old_logprob[t] map state/position[t] to "
            "state/position[t+1]; indices are zero-based"
        ),
        "evaluation_seed_base": EVALUATION_SEED_BASE,
        "reward_units": {"training": "native R / train_N=6",
                         "J": "test_N * scalar_return / horizon"},
        "entropy_measurement": {
            "analytic_raw_gaussian": "sum(log_sigma)+1.5*log(2*pi*e)",
            "aligned_exposure": "rollout r uses before-update value; after45 is final policy",
            "analytic_raw_entropy_is_clipped_action_entropy": False,
            "legacy_action_entropy_at_lambda0_is_measurement": False,
        },
        "runtime": {
            "python": sys.version, "torch": torch.__version__, "numpy": np.__version__,
            "device": "cpu", "dtype": "float32", "torch_threads": spec.torch_threads,
            "thread_environment": {name: os.environ.get(name) for name in (
                "OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS", "NUMEXPR_NUM_THREADS",
            )},
        },
    }

    def publish(boundary: str) -> None:
        summary["last_boundary"] = boundary
        summary["command_wall_seconds"] = time.perf_counter() - command_start
        summary["run_fit_wall_seconds"] = time.perf_counter() - started
        write_json(out / "summary.json", summary)

    publish("admitted")
    envs, agent, hooks, calls, control = [], None, [], {}, None
    try:
        if control_binding is not None:
            control = _read_control(
                control_binding, cell, launch_sha, spec, summary["control_binding"]
            )
        torch.set_num_threads(spec.torch_threads)
        seed_rng(cell.seed)
        envs = make_envs(spec.train_lanes, cell.seed, spec.train_n, spec.horizon)
        config = make_b05_config(cell, envs, spec)
        _assert_config_contract(config, cell)
        summary["config"] = b05_config_dict(config)
        if control is not None:
            _compare_control_config(summary["config"], control, summary["control_binding"])
        summary["action_distribution"] = {
            "kind": str(getattr(config, "continuous_action_distribution", "gaussian")),
            "lambda_l": float(config.lambda_l),
            "entropy_targets_enabled": bool(config.use_entropy_targets),
            "entropy_annealing_enabled": bool(config.use_entropy_annealing),
            "mapping_is_environment_only": True,
        }
        write_json(out / "config.json", {
            "launch_sha": launch_sha, "cell": vars(cell), "spec": vars(spec),
            "config": summary["config"],
        })
        agent = build_agent(config, str(out / "learner_logs"))
        if agent_setup_hook is not None:
            agent_setup_hook(agent)
        calls, hooks = optimizer_counts(agent)
        summary["optimizer_calls"] = calls
        summary["effective_entropy_contract"] = assert_agent_entropy_contract(agent, cell)
        summary["logstd_optimizer_contract"] = b04.logstd_optimizer_contract(agent)
        summary["parameter_counts"] = {
            name: sum(parameter.numel() for parameter in module.parameters())
            for name, module in model_modules(agent).items()
        }
        initial_parameters = capture_parameters(agent)
        observed_initial = digest_agent(agent)
        summary["observed_initial_parameter_normalizer_digest"] = observed_initial
        if control is not None:
            summary["control_binding"]["candidate_initial_digest"] = observed_initial
            summary["control_binding"]["initial_digest_match"] = (
                observed_initial == summary["control_binding"]["control_initial_digest"]
            )
            if not summary["control_binding"]["initial_digest_match"]:
                raise ValueError("B05 initial parameter/normalizer digest mismatch")
        summary["initial_raw_sigma"] = b04.raw_sigma(agent)
        summary["initial_raw_log_sigma"] = b04.raw_log_sigma(agent)
        summary["initial_analytic_raw_entropy"] = b04.analytic_raw_entropy(
            summary["initial_raw_log_sigma"]
        )
        agent.train(True)
        summary["checkpoints"].append(save_checkpoint(agent, out, 0, config, launch_sha))
        evaluate_panel(agent, cell, 0, out, summary, spec, publish)
        states, observations = reset_all(envs)
        steps = np.zeros(spec.train_lanes, dtype=np.int64)
        dones = np.zeros(spec.train_lanes, dtype=bool)
        summary["status"], summary["fit_started"] = "training", True
        publish("training starts")
        for rollout in range(1, spec.rollouts + 1):
            rollout_start = time.perf_counter()
            optimizer_before = calls.copy()
            sigma_before = b04.raw_sigma(agent)
            states, observations, steps, dones, motion, returns = b04.collect_rollout(
                agent, envs, states, observations, steps, dones, cell, rollout, summary, spec,
                optimizer_calls_before=optimizer_before, training_step_hook=training_step_hook,
            )
            publish(f"rollout {rollout} collected")
            log_sigma_before = b04.raw_log_sigma(agent)
            summary["_active_training_rollout"].update(
                phase="updating", raw_sigma_before_update=sigma_before,
                raw_log_sigma_before_update=log_sigma_before,
                analytic_raw_entropy_before_update=b04.analytic_raw_entropy(log_sigma_before),
                optimizer_calls_before_update=optimizer_before,
            )
            if rollout == 1 and control is not None:
                _require_pre_update_control_match(summary, control, summary["control_binding"])
                publish("control matched before first update")
            losses = agent.update(
                last_values=np.zeros((spec.train_lanes, spec.train_n), dtype=np.float32),
                dones=dones.copy(), steps_in_buffer=spec.horizon, last_state=states.copy(),
                last_observations=observations.copy(),
            )
            summary["counts"]["updates"] += 1
            finite(losses, "B05 training losses")
            _assert_config_contract(agent.config, cell)
            assert_agent_entropy_contract(agent, cell)
            motion_parameters = parameter_motion(agent, initial_parameters)
            log_sigma_after = b04.raw_log_sigma(agent)
            row = {
                "rollout": rollout, "team_steps": summary["counts"]["training_team_steps"],
                "training_scalar_returns": returns.tolist(), "losses": jsonable(losses),
                "optimizer_delta": {name: calls[name] - optimizer_before[name] for name in calls},
                "optimizer_total": calls.copy(), "parameter_motion": motion_parameters,
                "raw_sigma_before_update": sigma_before,
                "raw_sigma_after_update": b04.raw_sigma(agent),
                "raw_log_sigma_before_update": log_sigma_before,
                "raw_log_sigma_after_update": log_sigma_after,
                "analytic_raw_entropy_before_update": b04.analytic_raw_entropy(log_sigma_before),
                "analytic_raw_entropy_after_update": b04.analytic_raw_entropy(log_sigma_after),
                "action_motion_telemetry": motion,
                "rollout_wall_seconds": time.perf_counter() - rollout_start,
            }
            with (out / "training.jsonl").open("a", encoding="utf-8") as stream:
                stream.write(json.dumps(jsonable(row), allow_nan=False) + "\n")
            summary["rollouts"].append(row)
            summary["parameter_motion"] = motion_parameters
            agent.clear_buffers()
            summary.pop("_active_training_rollout", None)
            publish(f"rollout {rollout} updated")
            if rollout in spec.panels:
                summary["checkpoints"].append(save_checkpoint(agent, out, rollout, config, launch_sha))
                evaluate_panel(agent, cell, rollout, out, summary, spec, publish)
        if summary["counts"] != _expected_counts(spec):
            raise ValueError("B05 training/evaluation exposure incomplete")
        expected_optimizer_calls = _expected_set_optimizer_calls(spec)
        if calls != expected_optimizer_calls:
            raise ValueError("B05 SET optimizer exposure differs from fixed config/spec")
        for name in ("discoverer_actor", "discoverer_critic"):
            if summary["parameter_motion"][name]["delta_l2"] <= 0:
                raise ValueError(f"required B05 learner module did not update: {name}")
        summary["pooled_action_motion_telemetry"] = pooled_motion(summary["rollouts"])
        if control is not None:
            summary["control_comparisons"], summary["final_control_comparison"] = (
                build_control_comparisons(summary, control, spec)
            )
        summary["final_parameter_normalizer_digest"] = digest_agent(agent)
        summary["final_raw_sigma"] = b04.raw_sigma(agent)
        summary["final_raw_log_sigma"] = b04.raw_log_sigma(agent)
        summary["final_analytic_raw_entropy"] = b04.analytic_raw_entropy(
            summary["final_raw_log_sigma"]
        )
        summary["status"] = "complete"
        return_code = 0
    except Exception as exc:
        active = summary.pop("_active_training_rollout", None)
        if active is not None:
            if "_telemetry" in active:
                telemetry = active.pop("_telemetry")
                component_sums = active.pop("component_sums")
                active["action_motion_telemetry_partial"] = b04._finish_motion(
                    telemetry, spec.train_n
                )
                active["native_component_sums_partial"] = jsonable(component_sums)
            active["phase"] = active["phase"] + "_failed"
            active["optimizer_calls_observed"] = calls.copy()
            before = active.get("optimizer_calls_before_update", {})
            active["optimizer_delta_observed"] = {
                name: count - int(before.get(name, 0)) for name, count in calls.items()
            }
            if agent is not None:
                active["entropy_observed_after_failure"] = b04.failure_entropy_snapshot(agent)
            summary["incomplete_rollout"] = jsonable(active)
        summary.update(status="failed", failure=f"{type(exc).__name__}: {exc}")
        (out / "error.txt").write_text(traceback.format_exc(), encoding="utf-8")
        return_code = 1
    finally:
        for hook in hooks:
            hook.remove()
        for env in envs:
            env.close()
        usage = resource.getrusage(resource.RUSAGE_SELF)
        summary["resources"] = {
            "command_wall_seconds": time.perf_counter() - command_start,
            "run_fit_wall_seconds": time.perf_counter() - started,
            "cpu_user_seconds": usage.ru_utime, "cpu_system_seconds": usage.ru_stime,
            "peak_rss_kib": usage.ru_maxrss,
            "rss_scope": "scientific process Linux RUSAGE_SELF",
            "resources_unmeasured": ["peak_scratch_bytes"],
        }
        publish(summary["status"])
    return return_code
