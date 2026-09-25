"""One fresh H6/clip/.05 fit against the immutable B05 SET/.05 record."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import resource
import subprocess
import sys
import time
import traceback
from typing import Any, Callable, Mapping

import numpy as np
import torch

from experiments.candidates.agent_count_generalization.action_law_b03 import runner as b03
from experiments.candidates.agent_count_generalization.adapter import make_envs
from experiments.candidates.agent_count_generalization.configuration import (
    DEFAULT_SPEC,
    DIRECTION,
    FitSpec,
    config_dict,
    make_config,
)
from experiments.candidates.agent_count_generalization.entropy_b04 import runner as b04
from experiments.candidates.agent_count_generalization.entropy_b05 import runner as b05
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


OBJECT_ID = "s1_bounded_package_b07"
TAG = "s1_bounded_package_b07_h6_l05_s952201"
EVALUATION_SEED_BASE = 1_500_000
REPOSITORY_ROOT = Path(__file__).resolve().parents[4]


@dataclass(frozen=True)
class TrainingCell:
    key: str = "h6_l05"
    arm: str = "H6"
    law: str = "clip"
    seed: int = 952201
    tag: str = TAG
    lambda_l: float = .05


CELL = TrainingCell()


@dataclass(frozen=True)
class ControlSpec:
    tag: str = "s1_entropy_b05_set_l05_s953201"
    object_id: str = "s1_entropy_b05"
    source_sha: str = "e2ea736457e0992fb53cf21aa775fd15da3d8231"
    seed: int = 953201
    summary_sha256: str = "136d090b32a8c5fec1eefad5dbaaefa9155d44ce4335c7fb0f07585d36cff4c4"
    checkpoint_name: str = "checkpoint_45.pt"
    checkpoint_sha256: str = "98062b5b338b684219c43b5c9a3dc13bf176322a948c439294beee1d52ae477e"
    checkpoint_bytes: int = 20_968_771


CONTROL = ControlSpec()


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _config_dict(config: Any) -> dict[str, Any]:
    return {
        **config_dict(config),
        "lambda_l_initial": float(config.lambda_l_initial),
        "lambda_l_final": float(config.lambda_l_final),
        "use_entropy_annealing": bool(config.use_entropy_annealing),
        "use_entropy_targets": bool(config.use_entropy_targets),
    }


def make_b07_config(envs: list[Any], spec: FitSpec = DEFAULT_SPEC, *, n: int | None = None) -> Any:
    config = make_config("H6", envs, CELL.seed, spec)
    config.lambda_l = config.lambda_l_initial = config.lambda_l_final = CELL.lambda_l
    config.use_entropy_annealing = False
    config.use_entropy_targets = False
    config.validate_config()
    _assert_config(config, expected_n=spec.train_n if n is None else n)
    return config


def _assert_config(config: Any, *, expected_n: int) -> None:
    if str(config.count_arm) != "H6" or int(config.n_agents) != expected_n or int(config.k) != 10:
        raise ValueError("B07 requires the unchanged H6 package, roster and k10 clock")
    if str(getattr(config, "continuous_action_distribution", "gaussian")) != "gaussian":
        raise ValueError("B07 requires the raw Gaussian policy distribution")
    if any(float(value) != .05 for value in (
        config.lambda_l, config.lambda_l_initial, config.lambda_l_final,
    )) or config.use_entropy_annealing or config.use_entropy_targets:
        raise ValueError("B07 entropy coefficient/endpoints/flags changed")


def _panel_world_seed(rollout: int, n: int) -> int:
    return EVALUATION_SEED_BASE + 1000 * rollout + 100 * n


def _expected_counts(spec: FitSpec) -> dict[str, int]:
    panel_count = len(spec.panels) * len(spec.test_ns)
    training = spec.rollouts * spec.train_lanes * spec.horizon
    evaluation = panel_count * spec.eval_lanes * spec.horizon
    return {
        "training_team_steps": training,
        "stored_team_steps": training,
        "training_uav_steps": training * spec.train_n,
        "training_episodes": spec.rollouts * spec.train_lanes,
        "terminal_resets": spec.rollouts * spec.train_lanes,
        "updates": spec.rollouts,
        "training_policy_step_calls": spec.rollouts * spec.horizon,
        "evaluation_team_steps": evaluation,
        "evaluation_episodes": panel_count * spec.eval_lanes,
        "evaluation_uav_steps": (
            len(spec.panels) * spec.eval_lanes * spec.horizon * sum(spec.test_ns)
        ),
        "evaluation_policy_step_calls": panel_count * spec.horizon,
    }


def _expected_h6_optimizer_calls() -> dict[str, int]:
    return {
        "coordinator": 675,
        "discoverer_actor": 101_250,
        "discoverer_critic": 101_250,
        "team_discriminator": 675,
        "individual_discriminator": 2_700,
    }


def _expected_control_worlds(spec: FitSpec) -> dict[tuple[int, int], list[int]]:
    return {
        (rollout, n): list(range(
            _panel_world_seed(rollout, n),
            _panel_world_seed(rollout, n) + spec.eval_lanes,
        ))
        for rollout in spec.panels for n in spec.test_ns
    }


def _read_control_summary(
    control: ControlSpec, *, summary_root: Path, committed: bool,
) -> tuple[dict[str, Any], dict[str, Any]]:
    path = Path(summary_root) / control.tag / "summary.json"
    if committed:
        relative = Path("runs") / DIRECTION / control.tag / "summary.json"
        raw = subprocess.run(
            ["git", "-C", str(REPOSITORY_ROOT), "show", f"HEAD:{relative.as_posix()}"],
            check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        ).stdout
        if path.read_bytes() != raw:
            raise ValueError("B07 committed/working SET summary bytes differ")
        binding = "HEAD git blob plus identical working bytes"
    else:
        raw = path.read_bytes()
        binding = "pytest fixture bytes"
    digest = hashlib.sha256(raw).hexdigest()
    if digest != control.summary_sha256:
        raise ValueError("B07 SET summary SHA-256 mismatch")
    summary = json.loads(raw)
    if not isinstance(summary, dict):
        raise ValueError("B07 SET summary is not an object")
    return summary, {"path": str(path), "sha256": digest, "bytes": len(raw), "binding": binding}


def _validate_control(
    checkpoint: Path, *, control: ControlSpec = CONTROL, spec: FitSpec = DEFAULT_SPEC,
    summary_root: Path = REPOSITORY_ROOT / "runs" / DIRECTION,
    committed_summary: bool = True,
) -> tuple[dict[str, Any], dict[str, Any]]:
    summary, summary_identity = _read_control_summary(
        control, summary_root=summary_root, committed=committed_summary,
    )
    expected_identity = {
        "status": "complete", "object_id": control.object_id,
        "launch_sha": control.source_sha, "tag": control.tag, "arm": "SET",
        "training_action_law": "clip", "seed": control.seed,
    }
    if any(summary.get(key) != value for key, value in expected_identity.items()):
        raise ValueError("B07 SET status/source/object identity mismatch")
    cell = summary.get("cell", {})
    if cell.get("key") != "set_l05" or cell.get("tag") != control.tag:
        raise ValueError("B07 SET cell identity mismatch")
    if cell.get("seed") != control.seed or cell.get("arm") != "SET" or cell.get("law") != "clip":
        raise ValueError("B07 SET cell package mismatch")
    if cell.get("lambda_l") != .05 or summary.get("spec") != jsonable(vars(spec)):
        raise ValueError("B07 SET coefficient/spec mismatch")
    if summary.get("fit_started") is not True or summary.get("evaluation_seed_base") != EVALUATION_SEED_BASE:
        raise ValueError("B07 SET fit/evaluation contract incomplete")
    if summary.get("training_world_seeds") != list(range(control.seed, control.seed + spec.train_lanes)):
        raise ValueError("B07 SET training worlds mismatch")
    if summary.get("counts") != b05._expected_counts(spec):
        raise ValueError("B07 SET exposure counts mismatch")
    training_config = summary.get("config", {})
    architecture = {
        "count_arm": "SET", "seed": control.seed, "n_agents": spec.train_n,
        "hidden_size": spec.hidden_size, "n_heads": spec.n_heads,
        "n_encoder_layers": spec.n_layers, "n_decoder_layers": spec.n_layers,
        "ppo_epochs": spec.ppo_epochs, "sequence_batch_size": spec.sequence_batch_size,
        "coordinator_batch_size": spec.coordinator_batch_size,
        "lambda_l": .05, "lambda_l_initial": .05, "lambda_l_final": .05,
        "use_entropy_annealing": False, "use_entropy_targets": False,
    }
    if any(training_config.get(key) != value for key, value in architecture.items()):
        raise ValueError("B07 SET effective configuration/architecture mismatch")
    expected_worlds = _expected_control_worlds(spec)
    panels: dict[tuple[int, int], dict[str, Any]] = {}
    for row in summary.get("panels", []):
        try:
            key = (int(row["after_rollout"]), int(row["test_n"]))
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError("B07 SET panel identity invalid") from exc
        if key in panels or key not in expected_worlds:
            raise ValueError("B07 SET panel set contains duplicate/unplanned entry")
        if row.get("world_seeds") != expected_worlds[key]:
            raise ValueError(f"B07 SET panel worlds mismatch at {key}")
        if not b05._control_panel_payload_valid(
            row, rollout=key[0], n=key[1], spec=spec, training_config=training_config,
        ):
            raise ValueError(f"B07 SET panel payload/config invalid at {key}")
        panels[key] = row
    if set(panels) != set(expected_worlds):
        raise ValueError("B07 SET does not contain exactly all planned stage/N panels")
    checkpoint_rows = [
        row for row in summary.get("checkpoints", []) if row.get("path") == control.checkpoint_name
    ]
    if len(checkpoint_rows) != 1 or checkpoint_rows[0].get("sha256") != control.checkpoint_sha256 \
            or checkpoint_rows[0].get("bytes") != control.checkpoint_bytes:
        raise ValueError("B07 SET committed checkpoint identity mismatch")
    checkpoint = Path(checkpoint)
    if not checkpoint.is_file() or checkpoint.stat().st_size != control.checkpoint_bytes:
        raise ValueError("B07 SET checkpoint byte-size mismatch")
    checkpoint_digest = file_sha256(checkpoint)
    if checkpoint_digest != control.checkpoint_sha256:
        raise ValueError("B07 SET checkpoint SHA-256 mismatch")
    identity = {
        "summary": summary_identity,
        "checkpoint": {"path": str(checkpoint), "sha256": checkpoint_digest,
                       "bytes": checkpoint.stat().st_size},
        "source_sha": control.source_sha, "tag": control.tag,
        "checkpoint_loaded": False, "panels_validated": len(panels),
    }
    return summary, identity


def _compare_panel(candidate: dict[str, Any], control: dict[str, Any]) -> dict[str, Any]:
    key = (int(candidate["after_rollout"]), int(candidate["test_n"]))
    if candidate["world_seeds"] != control["world_seeds"]:
        raise ValueError(f"B07 candidate/control world mismatch at {key}")
    h6_j = np.asarray(candidate["J"], dtype=np.float64)
    set_j = np.asarray(control["J"], dtype=np.float64)
    if h6_j.shape != set_j.shape or not np.isfinite((h6_j, set_j)).all():
        raise ValueError(f"B07 candidate/control J payload invalid at {key}")
    delta_j = h6_j - set_j
    components = {}
    for name in COMPONENTS:
        h6 = np.asarray(candidate["component_means"][name], dtype=np.float64)
        baseline = np.asarray(control["component_means"][name], dtype=np.float64)
        if h6.shape != baseline.shape or not np.isfinite((h6, baseline)).all():
            raise ValueError(f"B07 candidate/control {name} payload invalid at {key}")
        delta = h6 - baseline
        components[name] = {
            "h6_per_world": h6.tolist(), "set_l05_per_world": baseline.tolist(),
            "h6_minus_set_per_world": delta.tolist(), "h6_minus_set_mean": float(delta.mean()),
        }
        if name == "coverage_reward":
            components[name]["served_users_per_step_difference"] = float(50 * delta.mean())
    return {
        "after_rollout": key[0], "test_n": key[1], "world_seeds": candidate["world_seeds"],
        "h6_J_per_world": h6_j.tolist(), "set_l05_J_per_world": set_j.tolist(),
        "h6_minus_set_J_per_world": delta_j.tolist(),
        "h6_minus_set_J_mean": float(delta_j.mean()),
        "world_signs": {"positive": int((delta_j > 0).sum()),
                        "zero": int((delta_j == 0).sum()),
                        "negative": int((delta_j < 0).sum())},
        "component_comparisons": components,
    }


def _final_comparison(rows: list[dict[str, Any]], final_rollout: int) -> dict[str, Any]:
    final = {int(row["test_n"]): row for row in rows if row["after_rollout"] == final_rollout}
    if set(final) != {4, 6, 8}:
        raise ValueError("B07 final comparison lacks fixed N4/N6/N8 panels")
    d = {n: float(final[n]["h6_minus_set_J_mean"]) for n in final}
    coverage = {
        n: float(final[n]["component_comparisons"]["coverage_reward"]["h6_minus_set_mean"])
        for n in final
    }
    d_u = (d[4] + d[8]) / 2
    return {
        "after_rollout": final_rollout,
        "by_test_n": {str(n): {
            "D_J_h6_minus_set": d[n], "D_coverage_h6_minus_set": coverage[n],
            "served_users_per_step_difference": 50 * coverage[n],
            "world_signs": final[n]["world_signs"],
        } for n in sorted(final)},
        "D_U_equal_weight_N4_N8": d_u,
        "full_directional_pattern": (
            d[4] > 0 and coverage[4] > 0 and d[8] > 0 and coverage[8] > 0
            and d[6] >= 0 and coverage[6] >= 0 and d_u > 0
        ),
        "scope": "fresh H6 seed952201 minus immutable SET seed953201 on same stage/world panels",
    }


def _source_paths() -> tuple[Path, ...]:
    return (
        Path(__file__).resolve(),
        REPOSITORY_ROOT / "scripts" / "run_agent_count_bounded_package_b07.py",
        REPOSITORY_ROOT / "experiments/candidates/agent_count_generalization/action_law_b03/runner.py",
        REPOSITORY_ROOT / "experiments/candidates/agent_count_generalization/entropy_b04/runner.py",
        REPOSITORY_ROOT / "experiments/candidates/agent_count_generalization/entropy_b05/runner.py",
        REPOSITORY_ROOT / "experiments/candidates/agent_count_generalization/configuration.py",
        REPOSITORY_ROOT / "experiments/candidates/agent_count_generalization/models.py",
        REPOSITORY_ROOT / "experiments/candidates/agent_count_generalization/runner.py",
        REPOSITORY_ROOT / "experiments/candidates/agent_count_generalization/adapter.py",
    )


def _source_hashes() -> dict[str, str]:
    return {path.relative_to(REPOSITORY_ROOT).as_posix(): file_sha256(path) for path in _source_paths()}


class _CountingAgent:
    def __init__(self, agent: Any, counts: dict[str, int], summary: dict[str, Any]):
        self._agent = agent
        self._counts = counts
        self._summary = summary
        self.optimizer_before: dict[str, int] = {}

    def __getattr__(self, name: str) -> Any:
        return getattr(self._agent, name)

    def step(self, *args: Any, **kwargs: Any) -> Any:
        active = self._summary.get("_active_training_rollout")
        if active is not None:
            active.setdefault("optimizer_calls_before_update", self.optimizer_before.copy())
        result = self._agent.step(*args, **kwargs)
        self._counts["training_policy_step_calls"] += 1
        return result


def evaluate_panel(
    learner: Any, rollout: int, out: Path, summary: dict[str, Any], spec: FitSpec,
    publish: Callable[[str], None], control_panels: Mapping[tuple[int, int], dict[str, Any]],
) -> None:
    learner_model_before = digest_agent(learner)
    learner_runtime_before = b03.runtime_state_digest(learner)
    learner_rng_before = b03._rng_digest()
    evaluated_rows: list[dict[str, Any]] = []
    with preserve_rng():
        for n in spec.test_ns:
            world_seed = _panel_world_seed(rollout, n)
            seed_rng(world_seed + 51)
            envs = make_envs(spec.eval_lanes, world_seed, n, spec.horizon)
            target, hooks = None, []
            row = {
                "after_rollout": rollout,
                "training_team_steps": rollout * spec.train_lanes * spec.horizon,
                "test_n": n, "world_seeds": list(range(world_seed, world_seed + spec.eval_lanes)),
                "execution_law": "clip", "status": "running", "steps": 0,
                "episodes": 0, "policy_step_calls": 0,
            }
            summary["panels"].append(row)
            evaluated_rows.append(row)
            publish(f"evaluation {rollout} N={n} starting")
            try:
                config = make_b07_config(envs, spec, n=n)
                target = build_agent(config, str(out / "evaluation_logs" / f"r{rollout}_n{n}"))
                strict_sync(target, learner)
                target.train(False)
                for lane in range(spec.eval_lanes):
                    target.reset_env_state(lane)
                calls, hooks = optimizer_counts(target)
                target_before = digest_agent(target)
                strict_sync_match = target_before == learner_model_before
                if not strict_sync_match:
                    raise ValueError("B07 evaluation target did not strictly match learner")
                states, observations = reset_all(envs)
                steps = np.zeros(spec.eval_lanes, dtype=np.int64)
                dones = np.zeros(spec.eval_lanes, dtype=bool)
                returns = np.zeros(spec.eval_lanes, dtype=np.float64)
                components = {name: np.zeros(spec.eval_lanes, dtype=np.float64) for name in COMPONENTS}
                executed_min, executed_max = float("inf"), float("-inf")
                diagnostics_rng_unchanged = True
                with torch.no_grad():
                    for t in range(spec.horizon):
                        raw_actions, _, data = target.step(
                            states, observations, steps, dones, deterministic=True,
                            return_step_data=True, build_infos=False,
                        )
                        row["policy_step_calls"] += 1
                        summary["counts"]["evaluation_policy_step_calls"] += 1
                        finite((raw_actions, data), "B07 evaluation policy output")
                        rng_before = b03._rng_digest()
                        raw_before = raw_actions.copy()
                        executed = np.clip(raw_actions, -1.0, 1.0)
                        diagnostics_rng_unchanged &= rng_before == b03._rng_digest()
                        if not np.array_equal(raw_actions, raw_before):
                            raise ValueError("B07 evaluation mapping mutated raw policy actions")
                        executed_min = min(executed_min, float(executed.min()))
                        executed_max = max(executed_max, float(executed.max()))
                        for lane, env in enumerate(envs):
                            obs, reward, term, trunc, info = env.step(executed[lane])
                            done = bool(term or trunc)
                            row["steps"] += 1
                            row["episodes"] += int(done)
                            summary["counts"]["evaluation_team_steps"] += 1
                            summary["counts"]["evaluation_episodes"] += int(done)
                            summary["counts"]["evaluation_uav_steps"] += n
                            parts = native_components(info, reward, n)
                            returns[lane] += reward
                            for name in COMPONENTS:
                                components[name][lane] += parts[name]
                            states[lane], observations[lane] = info["next_state"], obs
                            dones[lane] = done
                        steps += 1
                        if dones.any() and (t != spec.horizon - 1 or not dones.all()):
                            raise ValueError("unexpected B07 evaluation terminal boundary")
                if not dones.all():
                    raise ValueError("B07 evaluation missed fixed terminal boundary")
                means = {name: value / spec.horizon for name, value in components.items()}
                j = n * returns / spec.horizon
                native_j = (
                    .7 * means["coverage_reward"] + .3 * means["quality_reward"]
                    - means["energy_penalty"]
                )
                if not np.allclose(j, means["total_reward"], atol=1e-7, rtol=1e-6) \
                        or not np.allclose(j, native_j, atol=1e-7, rtol=1e-6):
                    raise ValueError("B07 evaluation native J/component identity failed")
                if any(calls.values()) or digest_agent(target) != target_before:
                    raise ValueError("B07 evaluation changed target parameters/normalizers")
                if not diagnostics_rng_unchanged or executed_min < -1.0 or executed_max > 1.0:
                    raise ValueError("B07 evaluation action diagnostic contract failed")
                row.update(
                    status="complete", J=j.tolist(), scalar_returns=returns.tolist(),
                    component_means=jsonable(means), optimizer_calls=calls.copy(),
                    frozen_weights_and_normalizers=True, strict_sync_digest_match=True,
                    target_parameter_normalizer_digest_before=target_before,
                    target_parameter_normalizer_digest_after=digest_agent(target),
                    diagnostics_rng_unchanged=True,
                    executed_action_bounds={"minimum": executed_min, "maximum": executed_max},
                    config=_config_dict(config),
                )
                comparison = _compare_panel(row, control_panels[(rollout, n)])
                row["control_comparison"] = comparison
                summary["control_comparisons"].append(comparison)
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
    learner_model_after = digest_agent(learner)
    learner_runtime_after = b03.runtime_state_digest(learner)
    learner_rng_after = b03._rng_digest()
    model_preserved = learner_model_after == learner_model_before
    runtime_preserved = learner_runtime_after == learner_runtime_before
    rng_preserved = learner_rng_after == learner_rng_before
    for row in evaluated_rows:
        row["learner_isolation"] = {
            "parameter_normalizer_digest_before": learner_model_before,
            "parameter_normalizer_digest_after": learner_model_after,
            "parameters_and_normalizers_preserved": model_preserved,
            "runtime_digest_before": learner_runtime_before,
            "runtime_digest_after": learner_runtime_after,
            "runtime_preserved": runtime_preserved,
            "global_rng_digest_before": learner_rng_before,
            "global_rng_digest_after": learner_rng_after,
            "global_rng_preserved": rng_preserved,
        }
        write_json(out / f"panel_{rollout:02d}_n{row['test_n']}.json", row)
    if not model_preserved:
        raise ValueError("B07 evaluation modified learner parameters/normalizers")
    if not runtime_preserved:
        raise ValueError("B07 evaluation modified learner runtime state")
    if not rng_preserved:
        raise ValueError("B07 evaluation modified learner/global RNG state")


def _control_identity_now(checkpoint: Path, summary_identity: dict[str, Any]) -> dict[str, Any]:
    checkpoint = Path(checkpoint)
    return {
        "summary": {"path": summary_identity["path"],
                    "sha256": file_sha256(Path(summary_identity["path"])),
                    "bytes": Path(summary_identity["path"]).stat().st_size},
        "checkpoint": {"path": str(checkpoint), "sha256": file_sha256(checkpoint),
                       "bytes": checkpoint.stat().st_size},
    }


def run_fit(
    out: Path, launch_sha: str, admission: dict[str, Any], control_checkpoint: Path,
    spec: FitSpec = DEFAULT_SPEC, *, control: ControlSpec = CONTROL,
    summary_root: Path = REPOSITORY_ROOT / "runs" / DIRECTION,
    committed_control_summary: bool = True, command_start: float | None = None,
    agent_setup_hook: Callable[[Any], None] | None = None,
    training_step_hook: Callable[[dict[str, Any]], None] | None = None,
) -> int:
    out = Path(out)
    if out.name != TAG:
        raise ValueError(f"B07 output basename must be {TAG}")
    if (out / "summary.json").exists():
        raise ValueError("existing B07 summary; reconcile original attempt")
    if tuple(spec.panels) != tuple(sorted(set(spec.panels))) or 0 not in spec.panels \
            or spec.rollouts != max(spec.panels):
        raise ValueError("B07 requires ordered stages including initialization and final rollout")
    out.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    command_start = started if command_start is None else command_start
    expected_counts = _expected_counts(spec)
    summary: dict[str, Any] = {
        "schema": 1, "object_id": OBJECT_ID, "direction": DIRECTION,
        "cell": jsonable(vars(CELL)), "arm": CELL.arm, "training_action_law": CELL.law,
        "seed": CELL.seed, "tag": TAG, "launch_sha": launch_sha, "admission": admission,
        "status": "validating_control", "fit_started": False, "failure": None,
        "pretrained_checkpoint_loaded": False, "expected_old_initial_digest": None,
        "spec": jsonable(vars(spec)), "panels": [], "checkpoints": [], "rollouts": [],
        "control_comparisons": [], "final_control_comparison": None,
        "control_identity_before": None, "control_identity_after": None,
        "counts": {key: 0 for key in expected_counts}, "expected_counts": expected_counts,
        "training_world_seeds": list(range(CELL.seed, CELL.seed + spec.train_lanes)),
        "evaluation_seed_base": EVALUATION_SEED_BASE, "evaluation_action_law": "clip",
        "reward_units": {"training": "native R / train_N=6",
                         "J": "test_N * scalar_return / horizon",
                         "coverage_cost": "50 * mean coverage fraction difference"},
        "transition_indexing": (
            "action[t] and old_logprob[t] map state/position[t] to state/position[t+1]"
        ),
        "source_hashes_before": _source_hashes(),
        "runtime": {"python": sys.version, "torch": torch.__version__, "numpy": np.__version__,
                    "device": "cpu", "dtype": "float32", "torch_threads": spec.torch_threads,
                    "thread_environment": {name: os.environ.get(name) for name in (
                        "OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS",
                        "NUMEXPR_NUM_THREADS",
                    )}},
    }

    def publish(boundary: str) -> None:
        summary["last_boundary"] = boundary
        summary["command_wall_seconds"] = time.perf_counter() - command_start
        summary["run_fit_wall_seconds"] = time.perf_counter() - started
        write_json(out / "summary.json", summary)

    publish("admitted")
    envs, agent, hooks, optimizer_call_counts = [], None, [], {}
    control_summary: dict[str, Any] | None = None
    try:
        control_summary, identity = _validate_control(
            control_checkpoint, control=control, spec=spec, summary_root=summary_root,
            committed_summary=committed_control_summary,
        )
        summary["control_identity_before"] = identity
        control_panels = {
            (int(row["after_rollout"]), int(row["test_n"])): row
            for row in control_summary["panels"]
        }
        publish("immutable SET control validated before fit")
        torch.set_num_threads(spec.torch_threads)
        seed_rng(CELL.seed)
        envs = make_envs(spec.train_lanes, CELL.seed, spec.train_n, spec.horizon)
        config = make_b07_config(envs, spec)
        summary["config"] = _config_dict(config)
        summary["effective_entropy_contract"] = {
            "lambda_l": float(config.lambda_l),
            "lambda_l_initial": float(config.lambda_l_initial),
            "lambda_l_final": float(config.lambda_l_final),
            "entropy_annealing_enabled": bool(config.use_entropy_annealing),
            "entropy_targets_enabled": bool(config.use_entropy_targets),
        }
        write_json(out / "config.json", {
            "launch_sha": launch_sha, "cell": vars(CELL), "spec": vars(spec),
            "config": summary["config"], "control": identity,
        })
        agent = build_agent(config, str(out / "learner_logs"))
        if agent_setup_hook is not None:
            agent_setup_hook(agent)
        optimizer_call_counts, hooks = optimizer_counts(agent)
        summary["optimizer_calls"] = optimizer_call_counts
        summary["parameter_counts"] = {
            name: sum(parameter.numel() for parameter in module.parameters())
            for name, module in model_modules(agent).items()
        }
        initial_parameters = capture_parameters(agent)
        summary["observed_initial_parameter_normalizer_digest"] = digest_agent(agent)
        summary["initial_raw_sigma"] = b03.raw_sigma(agent)
        summary["initial_raw_log_sigma"] = np.log(summary["initial_raw_sigma"]).tolist()
        agent.train(True)
        summary["checkpoints"].append(save_checkpoint(agent, out, 0, config, launch_sha))
        evaluate_panel(agent, 0, out, summary, spec, publish, control_panels)
        states, observations = reset_all(envs)
        steps = np.zeros(spec.train_lanes, dtype=np.int64)
        dones = np.zeros(spec.train_lanes, dtype=bool)
        summary["status"], summary["fit_started"] = "training", True
        publish("training starts")
        counted_agent = _CountingAgent(agent, summary["counts"], summary)
        for rollout in range(1, spec.rollouts + 1):
            rollout_start = time.perf_counter()
            optimizer_before = optimizer_call_counts.copy()
            counted_agent.optimizer_before = optimizer_before
            sigma_before = b03.raw_sigma(agent)
            states, observations, steps, dones, motion, returns = b03.collect_rollout(
                counted_agent, envs, states, observations, steps, dones, CELL, rollout,
                summary, spec, training_step_hook=training_step_hook,
            )
            summary["counts"]["training_uav_steps"] = (
                summary["counts"]["training_team_steps"] * spec.train_n
            )
            publish(f"rollout {rollout} collected")
            summary["_active_training_rollout"].update(
                phase="updating", raw_sigma_before_update=sigma_before,
                optimizer_calls_before_update=optimizer_before,
            )
            losses = agent.update(
                last_values=np.zeros((spec.train_lanes, spec.train_n), dtype=np.float32),
                dones=dones.copy(), steps_in_buffer=spec.horizon,
                last_state=states.copy(), last_observations=observations.copy(),
            )
            summary["counts"]["updates"] += 1
            finite(losses, "B07 training losses")
            _assert_config(agent.config, expected_n=spec.train_n)
            motion_parameters = parameter_motion(agent, initial_parameters)
            row = {
                "rollout": rollout, "team_steps": summary["counts"]["training_team_steps"],
                "training_scalar_returns": returns.tolist(), "losses": jsonable(losses),
                "optimizer_delta": {name: optimizer_call_counts[name] - optimizer_before[name]
                                    for name in optimizer_call_counts},
                "optimizer_total": optimizer_call_counts.copy(),
                "parameter_motion": motion_parameters,
                "raw_sigma_before_update": sigma_before,
                "raw_sigma_after_update": b03.raw_sigma(agent),
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
                evaluate_panel(agent, rollout, out, summary, spec, publish, control_panels)
        if summary["counts"] != expected_counts:
            raise ValueError(f"B07 exposure counts incomplete: {summary['counts']} != {expected_counts}")
        required = (
            "coordinator", "discoverer_actor", "discoverer_critic",
            "team_discriminator", "individual_discriminator",
        )
        for name in required:
            if optimizer_call_counts.get(name, 0) <= 0 or summary["parameter_motion"][name]["delta_l2"] <= 0:
                raise ValueError(f"required B07 H6 learner module did not update: {name}")
        if spec == DEFAULT_SPEC and optimizer_call_counts != _expected_h6_optimizer_calls():
            raise ValueError("B07 production H6 optimizer exposure differs from fixed contract")
        if len(summary["checkpoints"]) != len(spec.panels):
            raise ValueError("B07 checkpoint stage count incomplete")
        summary["final_parameter_normalizer_digest"] = digest_agent(agent)
        summary["final_raw_sigma"] = b03.raw_sigma(agent)
        summary["final_raw_log_sigma"] = np.log(summary["final_raw_sigma"]).tolist()
        summary["final_control_comparison"] = _final_comparison(
            summary["control_comparisons"], spec.rollouts,
        )
        summary["source_hashes_after"] = _source_hashes()
        summary["source_hashes_unchanged"] = summary["source_hashes_before"] == summary["source_hashes_after"]
        if not summary["source_hashes_unchanged"]:
            raise ValueError("B07 source bytes changed during fit")
        summary["control_identity_after"] = _control_identity_now(
            Path(control_checkpoint), identity["summary"],
        )
        summary["control_inputs_unchanged"] = (
            identity["summary"]["sha256"] == summary["control_identity_after"]["summary"]["sha256"]
            and identity["checkpoint"] == summary["control_identity_after"]["checkpoint"]
        )
        if not summary["control_inputs_unchanged"]:
            raise ValueError("B07 immutable SET inputs changed during fit")
        summary["status"] = "complete"
        return_code = 0
    except Exception as exc:
        summary["counts"]["training_uav_steps"] = (
            summary["counts"]["training_team_steps"] * spec.train_n
        )
        active = summary.pop("_active_training_rollout", None)
        if active is not None:
            if "_telemetry" in active:
                telemetry = active.pop("_telemetry")
                component_sums = active.pop("component_sums")
                active["action_motion_telemetry_partial"] = b03._finish_motion(
                    telemetry, spec.train_n,
                )
                active["native_component_sums_partial"] = jsonable(component_sums)
            active["phase"] = active["phase"] + "_failed"
            active["optimizer_calls_observed"] = optimizer_call_counts.copy()
            before = active.get("optimizer_calls_before_update", {})
            active["optimizer_delta_observed"] = {
                name: count - int(before.get(name, 0))
                for name, count in optimizer_call_counts.items()
            }
            if agent is not None:
                active["entropy_observed_after_failure"] = b04.failure_entropy_snapshot(agent)
            summary["incomplete_rollout"] = jsonable(active)
        summary.update(status="failed", failure=f"{type(exc).__name__}: {exc}")
        summary["source_hashes_after"] = _source_hashes()
        summary["source_hashes_unchanged"] = summary["source_hashes_before"] == summary["source_hashes_after"]
        if summary.get("control_identity_before") is not None:
            try:
                summary["control_identity_after"] = _control_identity_now(
                    Path(control_checkpoint), summary["control_identity_before"]["summary"],
                )
            except (OSError, ValueError) as identity_exc:
                summary["control_identity_after_error"] = f"{type(identity_exc).__name__}: {identity_exc}"
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
