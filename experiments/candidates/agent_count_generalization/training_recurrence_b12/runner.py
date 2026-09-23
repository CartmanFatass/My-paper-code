"""Train one fixed ordinary SET B12 cell and evaluate its final policy at N8 then N6."""
from __future__ import annotations

from dataclasses import dataclass, replace
import json
from pathlib import Path
import resource
import sys
import time
import traceback
from typing import Any, Callable

import numpy as np
import torch

from experiments.candidates.agent_count_generalization.action_law_b03 import runner as b03
from experiments.candidates.agent_count_generalization.adapter import make_envs
from experiments.candidates.agent_count_generalization.configuration import (
    DEFAULT_SPEC, DIRECTION, FitSpec,
)
from experiments.candidates.agent_count_generalization.runner import (
    OPTIMIZERS, capture_parameters, digest_agent, finite, jsonable, model_modules,
    optimizer_counts, parameter_motion, save_checkpoint, seed_rng, write_json,
)
from experiments.candidates.agent_count_generalization.training_condition_b11 import (
    runner as b11,
)


OBJECT_ID = "s1_training_recurrence_b12"
REPOSITORY_ROOT = Path(__file__).resolve().parents[4]
SEED = 963401
TRAINING_ENV_SEED_BASE = 964401
FINAL_ROLLOUT = b11.FINAL_ROLLOUT
EVALUATION_ORDER = b11.EVALUATION_ORDER


@dataclass(frozen=True)
class TrainingCell:
    key: str
    train_n: int
    tag: str
    arm: str = "SET"
    law: str = "clip"
    seed: int = SEED
    lambda_l: float = .05


CELLS = (
    TrainingCell("t6", 6, "s1_training_recurrence_b12_t6_s963401"),
    TrainingCell("t8", 8, "s1_training_recurrence_b12_t8_s963401"),
)
CELL_BY_KEY = {cell.key: cell for cell in CELLS}
B12_BASE_SPEC = replace(
    DEFAULT_SPEC, test_ns=EVALUATION_ORDER, eval_lanes=32, panels=(FINAL_ROLLOUT,),
)


def spec_for(cell: TrainingCell, base: FitSpec = B12_BASE_SPEC) -> FitSpec:
    return replace(base, train_n=cell.train_n, test_ns=EVALUATION_ORDER, panels=(base.rollouts,))


def make_b12_config(
    cell: TrainingCell, envs: list[Any], spec: FitSpec, *, expected_n: int | None = None,
) -> Any:
    """Bind the fresh B12 seed while retaining B11's ordinary-SET config contract."""
    return b11.make_b11_config(cell, envs, spec, expected_n=expected_n)


def construct_common_initialized_agent(
    actual_config: Any, log_root: Path, *, build_fn: Callable[[Any, str], Any] = b11.build_agent,
) -> tuple[Any, dict[str, Any]]:
    """Use B11's canonical-N6 synchronization with the B12-seeded config."""
    return b11.construct_common_initialized_agent(actual_config, log_root, build_fn=build_fn)


def _source_paths() -> tuple[Path, ...]:
    b12_paths = (
        Path(__file__).resolve(),
        Path(__file__).resolve().with_name("__init__.py"),
        REPOSITORY_ROOT / "scripts/run_agent_count_training_recurrence_b12.py",
    )
    return tuple(dict.fromkeys((*b12_paths, *b11._source_paths())))


def _source_hashes() -> dict[str, str]:
    return {
        path.relative_to(REPOSITORY_ROOT).as_posix(): b11.file_sha256(path)
        for path in _source_paths()
    }


def run_fit(
    out: Path, cell: TrainingCell, launch_sha: str, admission: dict[str, Any],
    spec: FitSpec, *, command_start: float | None = None,
    agent_setup_hook: Callable[[Any], None] | None = None,
    training_step_hook: Callable[[dict[str, Any]], None] | None = None,
) -> int:
    """Run one B12 fit with fresh training addresses and unchanged B11 mechanics."""
    out = Path(out)
    if cell not in CELLS or out.name != cell.tag:
        raise ValueError("B12 accepts only the fixed T6/T8 cell and matching output tag")
    if spec.train_n != cell.train_n or tuple(spec.test_ns) != EVALUATION_ORDER \
            or tuple(spec.panels) != (spec.rollouts,):
        raise ValueError("B12 spec must bind actual train N and final-only N8 then N6 evaluation")
    if (out / "summary.json").exists():
        raise ValueError("existing B12 summary; reconcile original attempt")
    out.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    command_start = started if command_start is None else command_start
    expected = b11._expected_counts(spec)
    summary: dict[str, Any] = {
        "schema": 1, "object_id": OBJECT_ID, "direction": DIRECTION,
        "cell": jsonable(vars(cell)), "arm": "SET", "training_action_law": "clip",
        "seed": cell.seed, "tag": cell.tag, "launch_sha": launch_sha,
        "admission": admission, "status": "initializing", "fit_started": False,
        "failure": None, "spec": jsonable(vars(spec)), "panels": [],
        "checkpoints": [], "rollouts": [], "counts": {key: 0 for key in expected},
        "expected_counts": expected,
        "training_world_seeds": list(range(
            TRAINING_ENV_SEED_BASE, TRAINING_ENV_SEED_BASE + spec.train_lanes,
        )),
        "evaluation_order": list(EVALUATION_ORDER), "evaluation_action_law": "clip",
        "source_hashes_before": _source_hashes(),
        "reward_units": {
            "training": f"native R / train_N={cell.train_n}",
            "J": "test_N * scalar_return / horizon",
            "service": "users per post-transition step",
        },
        "transition_indexing": (
            "action[t] and original old_logprob[t] map state/position[t] to post-transition t+1"
        ),
        "runtime": {
            "python": sys.version, "torch": torch.__version__, "numpy": np.__version__,
            "device": "cpu", "dtype": "float32", "torch_threads": spec.torch_threads,
        },
    }

    def publish(boundary: str) -> None:
        summary["last_boundary"] = boundary
        summary["command_wall_seconds"] = time.perf_counter() - command_start
        summary["run_fit_wall_seconds"] = time.perf_counter() - started
        write_json(out / "summary.json", summary)

    envs, agent, hooks, calls = [], None, [], {name: 0 for name in OPTIMIZERS}
    publish("admitted")
    try:
        torch.set_num_threads(spec.torch_threads)
        envs = make_envs(spec.train_lanes, TRAINING_ENV_SEED_BASE, cell.train_n, spec.horizon)
        b11._assert_native_envs(envs, cell.train_n)
        seed_rng(cell.seed)
        config = make_b12_config(cell, envs, spec)
        summary["config"] = b11._config_record(config)
        write_json(out / "config.json", {
            "launch_sha": launch_sha, "cell": vars(cell), "spec": vars(spec),
            "config": summary["config"],
        })
        agent, initialization = construct_common_initialized_agent(
            config, out / "initialization_logs",
        )
        summary["common_initialization"] = initialization
        if agent_setup_hook is not None:
            agent_setup_hook(agent)
        calls, hooks = optimizer_counts(agent)
        summary["optimizer_calls"] = calls
        summary["parameter_counts"] = {
            name: sum(parameter.numel() for parameter in module.parameters())
            for name, module in model_modules(agent).items()
        }
        initial_parameters = capture_parameters(agent)
        summary["observed_initial_parameter_normalizer_digest"] = digest_agent(agent)
        summary["effective_entropy_contract_initial"] = b11._assert_agent_entropy(agent, cell)
        summary["initial_raw_sigma"] = b03.raw_sigma(agent)
        summary["checkpoints"].append(save_checkpoint(agent, out, 0, config, launch_sha))
        pairs = [env.reset() for env in envs]
        states = np.stack([info["state"] for observation, info in pairs])
        observations = np.stack([observation for observation, info in pairs])
        steps = np.zeros(spec.train_lanes, dtype=np.int64)
        dones = np.zeros(spec.train_lanes, dtype=bool)
        summary["status"], summary["fit_started"] = "training", True
        summary["counts"]["fits"] = 1
        publish("training starts")
        counted = b11._CountingAgent(agent, summary["counts"], summary)
        b03_cell = b03.TrainingCell(1, cell.key, "SET", "clip", cell.seed, cell.tag)
        for rollout in range(1, spec.rollouts + 1):
            rollout_start = time.perf_counter()
            optimizer_before = calls.copy()
            counted.optimizer_before = optimizer_before
            sigma_before = b03.raw_sigma(agent)
            states, observations, steps, dones, motion, returns = b03.collect_rollout(
                counted, envs, states, observations, steps, dones, b03_cell, rollout,
                summary, spec, training_step_hook=training_step_hook,
            )
            summary["counts"]["training_agent_rows"] = (
                summary["counts"]["training_team_steps"] * cell.train_n
            )
            publish(f"rollout {rollout} collected")
            summary["_active_training_rollout"].update(
                phase="updating", raw_sigma_before_update=sigma_before,
                optimizer_calls_before_update=optimizer_before,
            )
            losses = agent.update(
                last_values=np.zeros((spec.train_lanes, cell.train_n), dtype=np.float32),
                dones=dones.copy(), steps_in_buffer=spec.horizon,
                last_state=states.copy(), last_observations=observations.copy(),
            )
            summary["counts"]["updates"] += 1
            finite(losses, "B12 training losses")
            b11._assert_config(agent.config, cell, cell.train_n)
            entropy_after = b11._assert_agent_entropy(agent, cell)
            motion_parameters = parameter_motion(agent, initial_parameters)
            row = {
                "rollout": rollout, "team_steps": summary["counts"]["training_team_steps"],
                "training_scalar_returns": returns.tolist(), "losses": jsonable(losses),
                "optimizer_delta": {name: calls[name] - optimizer_before[name] for name in calls},
                "optimizer_total": calls.copy(), "parameter_motion": motion_parameters,
                "raw_sigma_before_update": sigma_before,
                "raw_sigma_after_update": b03.raw_sigma(agent),
                "effective_entropy_contract_after_update": entropy_after,
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
        summary["checkpoints"].append(save_checkpoint(
            agent, out, spec.rollouts, config, launch_sha,
        ))
        b11.evaluate_final(agent, cell, out, summary, spec, publish)
        if summary["counts"] != expected:
            raise ValueError(f"B12 exposure mismatch: {summary['counts']} != {expected}")
        if calls["discoverer_actor"] <= 0 or calls["discoverer_critic"] <= 0:
            raise ValueError("B12 SET actor/critic optimizer did not run")
        if any(calls[name] for name in (
            "coordinator", "team_discriminator", "individual_discriminator",
        )):
            raise ValueError("B12 SET unexpectedly updated disabled skill modules")
        for name in ("discoverer_actor", "discoverer_critic"):
            if summary["parameter_motion"][name]["delta_l2"] <= 0:
                raise ValueError(f"B12 required learner module did not move: {name}")
        if spec == spec_for(cell) and calls != b11._expected_production_optimizer_calls(cell):
            raise ValueError("B12 production optimizer exposure differs from fixed contract")
        if len(summary["checkpoints"]) != 2 or [row["path"] for row in summary["checkpoints"]] != [
            "checkpoint_00.pt", f"checkpoint_{spec.rollouts:02d}.pt",
        ]:
            raise ValueError("B12 checkpoint contract requires untrained and final only")
        summary["final_parameter_normalizer_digest"] = digest_agent(agent)
        summary["effective_entropy_contract_final"] = b11._assert_agent_entropy(agent, cell)
        summary["final_raw_sigma"] = b03.raw_sigma(agent)
        summary["source_hashes_after"] = _source_hashes()
        summary["source_hashes_unchanged"] = (
            summary["source_hashes_before"] == summary["source_hashes_after"]
        )
        if not summary["source_hashes_unchanged"]:
            raise ValueError("B12 source bytes changed during fit")
        summary["status"] = "complete"
        return_code = 0
    except Exception as exc:
        summary["counts"]["training_agent_rows"] = (
            summary["counts"]["training_team_steps"] * cell.train_n
        )
        active = summary.pop("_active_training_rollout", None)
        if active is not None:
            if "_telemetry" in active:
                telemetry = active.pop("_telemetry")
                component_sums = active.pop("component_sums")
                active["action_motion_telemetry_partial"] = b03._finish_motion(
                    telemetry, cell.train_n,
                )
                active["native_component_sums_partial"] = jsonable(component_sums)
            active["phase"] = active["phase"] + "_failed"
            active["optimizer_calls_observed"] = calls.copy()
            before = active.get("optimizer_calls_before_update", {})
            active["optimizer_delta_observed"] = {
                name: value - int(before.get(name, 0)) for name, value in calls.items()
            }
            summary["incomplete_rollout"] = jsonable(active)
        summary.update(status="failed", failure=f"{type(exc).__name__}: {exc}")
        summary["source_hashes_after"] = _source_hashes()
        summary["source_hashes_unchanged"] = (
            summary["source_hashes_before"] == summary["source_hashes_after"]
        )
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
